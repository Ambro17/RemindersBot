#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s [%(funcName)s] %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

from bot.constants import NORMAL_EXIT, ERROR_EXIT
from bot.handlers.event_set import events_set
from bot.handlers.misc import start, default, ups_handler
from bot.handlers.remove_reminder import remove_reminders
from bot.handlers.repeat_reminder import repeat_reminder
from bot.handlers.reminders_set import reminders_set
from bot.handlers.set_check_timezone import change_timezone, check_timezone
from bot.handlers.show_reminders import see_user_reminders
from bot.jobs.job_loader import load_reminders
from bot.persistence.psqlpersistence import PSQLPersistence
from bot.utils import msg_admin


def main():
    bot_persistence = PSQLPersistence(os.environ['DATABASE_URL'])
    updater = Updater(os.environ['BOT_KEY'], persistence=bot_persistence)
    dp = updater.dispatcher

    start_handler = CommandHandler('start', start)
    fallback_handler = MessageHandler(Filters.all, default)

    # Load reminders that were lost on bot restart (job_queue is not persistent)
    loaded_reminders = load_reminders(updater.bot, updater.job_queue)
    logger.info(f"Recovered {loaded_reminders} reminders")

    # Add bot handlers
    dp.add_handler(start_handler)
    dp.add_handler(reminders_set)
    dp.add_handler(repeat_reminder)
    dp.add_handler(remove_reminders)
    dp.add_handler(see_user_reminders)
    dp.add_handler(change_timezone)
    dp.add_handler(check_timezone)
    dp.add_handler(events_set)

    # Add special handlers. Error handler and fallback handler.
    dp.add_error_handler(ups_handler)
    dp.add_handler(fallback_handler)

    logger.info('Up and running')
    msg_admin(updater.bot, "⚡️ I'm up and running ⚡️️")
    updater.start_polling()
    updater.idle()

    return NORMAL_EXIT


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        logger.error("An update broke the bot.", exc_info=True)
        sys.exit(ERROR_EXIT)
