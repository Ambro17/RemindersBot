import logging

from telegram.ext import CommandHandler

from bot.constants import MINUTE
from bot.utils import datetime_from_answer, init_reminder_context, _setup_reminder_and_reply

logger = logging.getLogger(__name__)

def quicky(update, context):
    user_offset = context.user_data.get('offset')
    msg = update.message

    if not user_offset:
        msg.reply_text('Please first set your current time with /setmytime')
        return
    if not context.args:
        msg.reply_text("Mmm not like that\n/q buy something, 20")
        return

    to_remind, sep, minutes = ' '.join(context.args).rpartition(',')
    if not to_remind:
        msg.reply_text("Please add a *comma* and delay time. i.e /q charge phone*,* 20", parse_mode='markdown')
        return
    try:
        requested_delay = int(minutes.strip()) * MINUTE
    except ValueError:
        msg.reply_text("Delay must be in minutes. i.e 60")
        return

    when = datetime_from_answer(requested_delay)
    job_context = init_reminder_context(
        to_remind, msg.from_user, msg.chat_id, user_offset, remind_date_iso=when.isoformat()
    )
    logger.info('Setting up a new reminder')
    try:
        _setup_reminder_and_reply(update, context.job_queue, job_context, when)
    except Exception:
        logger.exception('Error writing reminder')
        msg.reply_text("I'm not perfect ¯\\_(ツ)_/¯")

quick_reminder = CommandHandler('q', quicky)
