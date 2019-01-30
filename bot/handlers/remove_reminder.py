"""
    Handler that manages reminders removal
"""
import logging

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from bot.constants import READ_REMINDER
from bot.persistence.db_ops import remove_reminder

logger = logging.getLogger(__name__)


def rm_reminder(bot, update, args):
    logger.info("STARTED new reminder removal")
    if not args:
        update.effective_message.reply_text("🗑 Qué reminder queres borrar?", quote=False)
        logger.info("Waiting user input on what reminder to remove..")
        return READ_REMINDER

    reminder_key = ' '.join(args)
    return _delete_reminder(bot, update, reminder_key)


def rm_reminder_from_text(bot, update):
    reminder_key = update.message.text
    return _delete_reminder(bot, update, reminder_key)


def _delete_reminder(bot, update, reminder_key):
    msg = remove_reminder(
        text=reminder_key,
        user_id=str(update.message.from_user.id),
    )
    update.message.reply_text(msg, parse_mode='markdown')

    logger.info("ENDED reminder removal successfully")
    return ConversationHandler.END


remove_reminders = ConversationHandler(
    entry_points=[
        CommandHandler('delete', rm_reminder, pass_args=True),
        CommandHandler('borrar', rm_reminder, pass_args=True),
    ],
    states={
        READ_REMINDER: [MessageHandler(Filters.text, rm_reminder_from_text)]
    },
    fallbacks=[]
)