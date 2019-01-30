import logging
import random

from telegram import TelegramError

from bot.utils import msg_admin

logger = logging.getLogger(__name__)


def start(bot, update):
    update.message.reply_text(
        f'Hola! Soy @RRemindersBot y estoy para recordarte\n\n'
        f'/remind para setear un nuevo reminder\n'
        f'/reminders para ver los reminders guardados\n'
        f'/delete para borrar un reminder\n\n'
        f'Podés elegir dentro de cuanto querés ser '
        f'notificado desde las opciones o escribir '
        f'la fecha vos mismo.\n'
        f'También hay atajos /r = /recordar = /remind\n'
        f'/borrar = /delete\n'
        f'Proximamente habrá eventos recurrentes con '
        f'/event'
    )


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
            text='🧐 No te entiendo.. escribí /start para ver instrucciones de uso'
        )
