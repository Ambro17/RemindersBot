"""
    Handler that manages repeat policy on a reminder notification. Repeat or expire.
"""
import logging
import random

from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from bot.constants import READ_TIME_SELECTION, READ_CUSTOM_DATE
from bot.handlers.misc import cancel
from bot.keyboard import DONE, REMIND_AGAIN
from bot.jobs.db_ops import remove_reminder, get_reminders
from bot.handlers.remind import read_custom_date, read_time_selection_from_button
from bot.utils import msg_admin, init_reminder_context, _show_time_options, get_reminder_key_from_text

logger = logging.getLogger(__name__)


def handle_repeat_decision(update, context):
    # Get reminder key (user_id, text, date)
    logger.info("STARTED new repeat decision conversation")
    cbackquery = update.callback_query
    answer = cbackquery.data

    logger.info(f'Getting reminder key from text `{cbackquery.message.text}`')
    reminder_key = get_reminder_key_from_text(cbackquery.message.text)
    logger.info(f"Reminder key: {reminder_key!r}")

    if answer == DONE:
        CONGRATZ_ICON = random.choice('🥇🏆🏅🎖')
        update.callback_query.message.edit_text(
            f'Well done! {CONGRATZ_ICON}',
            reply_markup=None
        )
        try:
            remove_reminder(text=reminder_key, user_id=str(cbackquery.from_user.id))
        except Exception:
            msg_admin(f"Error deleting reminder {reminder_key} from {cbackquery.from_user.name}")

        logger.info("ENDED Conversation successfully")
        return ConversationHandler.END

    elif answer == REMIND_AGAIN:
        # Fetch reminder from db
        try:
            reminders = get_reminders(
                user_id=str(cbackquery.from_user.id),
                text=reminder_key,
            ).all()
        except Exception:
            logger.error('Reminder not found. %s', reminder_key)
            cbackquery.message.edit_text(
                "Boo 👻\n"
                f"Can't re-set reminder. Please do it manually with `/remind {reminder_key}`",
                parse_mode='markdown')
            return ConversationHandler.END

        logger.info(f"Found {len(reminders)} reminders under that key")
        if not reminders:
            cbackquery.message.edit_text('👻! Try again', reply_markup=None)
            logger.error('Conversation ended, no reminder found under that key.')
            return ConversationHandler.END

        reminder = reminders[0]
        logger.info(f"Reminder to repeat {reminder}")
        reminder_context = init_reminder_context(
            reminder.text,
            cbackquery.from_user,
            cbackquery.from_user.id,
            context.user_data.get('offset', 0)
        )
        context.chat_data.update(reminder_context)

        logger.info("Showing time options..")
        _show_time_options(update, from_remind_again=True)

        return READ_TIME_SELECTION
    else:
        logger.error(f"Unexpected callback data {answer}")
        cbackquery.message.edit_text(
            "🤨 I was expecting you to tell me if i should repeat the reminder or not.. Let's start over",
            reply_markup=None
        )
        logger.info("Conversation ended. Unexpected callback received when trying to decide repetition policy")
        return ConversationHandler.END


repeat_reminder = ConversationHandler(
    entry_points=[
        # Capture if the user is Done with the reminder, or wants to repeat it
        CallbackQueryHandler(handle_repeat_decision)],
    states={
        READ_TIME_SELECTION: [
            # Wait for user input on when s/he wants to be reminded
            CallbackQueryHandler(
                read_time_selection_from_button,
            )
        ],
        READ_CUSTOM_DATE: [
            # If user selected Custom option, wait until it writes a date as remind time
            MessageHandler(Filters.text, read_custom_date)
        ],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    name='Repeat reminder',
    persistent=True
)