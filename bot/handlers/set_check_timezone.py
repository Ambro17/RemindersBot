import logging
from datetime import datetime, timedelta
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

READ_TIMEZONE = 1
MINUTE = 60
HOUR = 60 * MINUTE

logger = logging.getLogger(__name__)

def prompt_timezone(bot, update):
    update.message.reply_markdown('Enter your current time in `d/m HH:MM` format')
    return READ_TIMEZONE


def _seconds_offset(user_time):
    utc_now = datetime.utcnow()
    user_now = utc_now.replace(day=user_time.day, month=user_time.month,
                               hour=user_time.hour, minute=user_time.minute)
    offset = user_now - utc_now
    return offset.total_seconds()

def _seconds_to_hour_n_minutes(seconds):
    h, rest = divmod(seconds, HOUR)
    m, rest = divmod(rest, MINUTE)
    return int(h), int(m)

def read_timezone(bot, update, user_data):
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
        user_data['offset'] = offset

        h_m = _seconds_to_hour_n_minutes(offset)
        update.message.reply_markdown(f'✅ Your UTC offset is `{h_m[0]}:{str(h_m[1]).zfill(2)}`')

    return ConversationHandler.END


change_timezone = ConversationHandler(
    entry_points=[
        # Capture if the user is Done with the reminder, or wants to repeat it
        CommandHandler('setmytime', prompt_timezone),
    ],
    states={
        READ_TIMEZONE: [
            # Wait for user input on what is his/her current time
            MessageHandler(Filters.text, read_timezone, pass_user_data=True)
        ],
    },
    fallbacks=[],
    name='Change timezone',
    persistent=True
)

def check_time(bot, update, user_data):
    offset = user_data.get('offset')
    if offset is None:
        text = "You haven't set your time yet. Do it with /setmytime"
    else:
        utc_now = datetime.utcnow()
        user_now = utc_now + timedelta(seconds=offset)
        text = user_now.strftime('Your time is: `%H:%M`')

    update.message.reply_markdown(text)


check_timezone = CommandHandler('mytime', check_time, pass_user_data=True)