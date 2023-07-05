#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
from bot.jobs.models import create_tables

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from bot.handlers.todo import add_todo_cmd, show_todos_cmd, mark_as_done_cmd

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s [%(funcName)s] %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

from bot.constants import NORMAL_EXIT, ERROR_EXIT
from bot.handlers.event import events_set
from bot.handlers.feedback import add_feedback
from bot.handlers.misc import start, default, ups_handler
from bot.handlers.delete import remove_reminders
from bot.handlers.quick import quick_reminder
from bot.handlers.repeat import repeat_reminder
from bot.handlers.remind import reminders_set
from bot.handlers.mytimezone import change_timezone, check_timezone
from bot.handlers.myreminders import see_user_reminders
from bot.jobs.job_loader import load_reminders
from bot.persistence.psqlpersistence import PSQLPersistence


def main():
    bot_persistence = PSQLPersistence(os.environ.get('DATABASE_URL', 'Missing'))
    updater = Updater(os.environ.get('BOT_KEY', 'Missing'), persistence=bot_persistence, use_context=True)
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
    dp.add_handler(add_feedback)
    dp.add_handler(quick_reminder)
    dp.add_handler(events_set)
    dp.add_handler(add_todo_cmd)
    dp.add_handler(show_todos_cmd)
    dp.add_handler(mark_as_done_cmd)

    # Add special handlers. Error handler and fallback handler.
    dp.add_error_handler(ups_handler)
    dp.add_handler(fallback_handler)

    logger.info('Up and running')
    updater.start_polling()
    updater.idle()

    return NORMAL_EXIT


if __name__ == '__main__':
    create_tables()
    try:
        sys.exit(main())
    except Exception as e:
        logger.error("An update broke the bot.", exc_info=True)
        sys.exit(ERROR_EXIT)
