import logging
from datetime import datetime, timedelta
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

READ_TIMEZONE = 1
MINUTE = 60
HOUR = 60 * MINUTE

logger = logging.getLogger(__name__)

def prompt_timezone(update, context):
    update.message.reply_markdown('Enter your current time in `d/m HH:MM` format')
    return READ_TIMEZONE


def _seconds_offset(user_time):
    utc_now = datetime.utcnow()
    user_now = utc_now.replace(day=user_time.day, month=user_time.month,
                               hour=user_time.hour, minute=user_time.minute)
    offset = user_now - utc_now
    return offset.total_seconds()

def _seconds_to_hour_n_minutes(seconds):
    # Floor division truncates to lower number.
    #  10 // 3 = 3
    # -10 // 4 = -4
    # So we work with absolute seconds.
    seconds = abs(seconds)
    h, rest = divmod(seconds, HOUR)
    m, rest = divmod(rest, MINUTE)
    return int(h), int(m)

def _offset_seconds_to_utc_shift(seconds):
    sign = '-' if seconds < 0 else '+'
    h, m = _seconds_to_hour_n_minutes(seconds)
    padded_mins = str(m).zfill(2)
    return f"{sign}{h}:{padded_mins}"

def read_timezone(update, context):
    try:
        user_time = datetime.strptime(update.message.text, '%d/%m %H:%M')
    except ValueError:
        update.message.reply_text('Invalid format. Try again.')
        return
    except Exception:
        update.message.reply_text('Error. Try again.')
        return
    else:
        offset = _seconds_offset(user_time)
        logger.info(f'User `{update.message.from_user.name}` seconds offset from utc is `{offset}`')
        context.user_data['offset'] = offset

        utc_offset = _offset_seconds_to_utc_shift(offset)
        update.message.reply_markdown(f'✅ Your UTC offset is `{utc_offset}`')

    return ConversationHandler.END


change_timezone = ConversationHandler(
    entry_points=[
        # Capture if the user is Done with the reminder, or wants to repeat it
        CommandHandler('setmytime', prompt_timezone),
    ],
    states={
        READ_TIMEZONE: [
            # Wait for user input on what is his/her current time
            MessageHandler(Filters.text, read_timezone)
        ],
    },
    fallbacks=[],
    name='Change timezone',
    persistent=True
)

def check_time(update, context):
    offset = context.user_data.get('offset')
    if offset is None:
        text = "You haven't set your time yet. Do it with /setmytime"
    else:
        utc_now = datetime.utcnow()
        user_now = utc_now + timedelta(seconds=offset)
        text = user_now.strftime(f'Your time is: `%H:%M`\n\n» UTC offset `{_offset_seconds_to_utc_shift(offset)}`')

    update.message.reply_markdown(text)


check_timezone = CommandHandler('mytime', check_time)