"""
    Handler that shows the reminders of a given user
"""

import logging

from telegram.ext import CommandHandler

from bot.persistence.db_ops import get_reminders
from bot.utils import isoformat_to_datetime

logger = logging.getLogger(__name__)


def show_user_reminders(bot, update):
    user = update.message.from_user
    logger.info(f"Showing user reminders to {user.name}")
    reminders = get_reminders(user_id=str(user.id), expired=False)

    def format_reminder(rem):
        width = 10
        datetime_obj = isoformat_to_datetime(rem.remind_time)
        date_text = datetime_obj.strftime('%d/%m/%Y %H:%M')
        return f"{rem.text:{width}} | `{date_text}`"

    logger.info("Formatting reminders..")
    text = '\n'.join(
        format_reminder(rem) for rem in reminders
    )
    update.message.reply_text(text or 'No reminders set yet', parse_mode='markdown')


see_user_reminders = CommandHandler('reminders', show_user_reminders)
