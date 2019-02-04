import logging
import random

from telegram import TelegramError
from telegram.ext import ConversationHandler

from bot.utils import msg_admin

logger = logging.getLogger(__name__)


def start(bot, update):
    update.message.reply_text("""
Hello! I'm @RRemindersBot and i'm here to remind you

My skills include:

/remind to set new reminders
/myreminders to show your current reminders
/delete to delete a reminder

Before setting a new reminder it is recommended that 
you set your timezone with 
/setmytime so reminders work as expected.
You can then check with
/mytime if it shows your current time

I also have a quick reminder shortcut:
/q something, 20
will let you set a reminder of _something_ in 20 minutes in just one message
""", parse_mode='markdown')


def ups_handler(bot, update, error):
    try:
        raise error
    except TelegramError:
        logger.exception("A Telegram error occurred")
    except Exception:
        logger.exception("A general error occurred")
    finally:
        update.effective_message.reply_text('Errors happen ¯\\_(ツ)_/¯')
        msg_admin(bot, 'An error occurred on the bot. Check the logs')


def default(bot, update):
    """If a user sends an unknown command, answer accordingly. But not always to avoid flooding"""
    if random.choice((0, 1)):
        bot.send_message(
            chat_id=update.effective_message.chat_id,
            text="I don't get you 🧐.. write /start to see what are my skills"
        )


def cancel(bot, update):
    update.effective_message.reply_text('Operation cancelled ✅')
    return ConversationHandler.END