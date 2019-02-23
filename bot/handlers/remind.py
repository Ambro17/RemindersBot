"""
    Handler that manages creation of new reminders
"""
import copy
import logging

import dateparser
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

from bot.constants import READ_REMINDER, READ_TIME_SELECTION, READ_CUSTOM_DATE, CUSTOM, MINUTE
from bot.handlers.misc import cancel
from bot.utils import (
    init_reminder_context,
    datetime_from_answer,
    _show_time_options,
    _setup_reminder_and_reply,
    utc_time_from_user_date,
    user_current_time,
)

logger = logging.getLogger(__name__)


def remind(bot, update, args, chat_data, user_data):
    """Initialize reminder context and ask for reminder if it isn't yet known"""
    logger.info('STARTED new /remind conversation')
    user_offset = user_data.get('offset')
    if not user_offset:
        update.message.reply_text('Please first set your current time with /setmytime')
        return ConversationHandler.END
    if not args:
        # If the user did not specify what to remind, ask him/her
        update.effective_message.reply_text("⏰ What do you want to remind?", quote=False)
        logger.info("Waiting for user input on what to remind..")
        return READ_REMINDER

    msg = update.message
    thing_to_remind = ' '.join(args)
    logger.info(f'Reminder args: {thing_to_remind}')

    context = init_reminder_context(thing_to_remind, msg.from_user, msg.chat_id, user_offset)
    chat_data.update(context)
    logger.info(f"Read '{thing_to_remind}' from {context['user_tag']}."
                f" Offering time options..")

    # User time selection will be captured by read_time_selection_from_button
    logger.info('Showing time options..')
    _show_time_options(update)
    return READ_TIME_SELECTION


def read_reminder(bot, update, chat_data, user_data):
    try:
        msg = update.message
        logger.info(f'Read user input: {msg.text}')
        context = init_reminder_context(msg.text, msg.from_user, msg.chat_id, user_data.get('offset', 0))
        chat_data.update(context)
        logger.info('Showing time options..')
        _show_time_options(update)

    except Exception:
        logger.info('User did not enter text.')
        update.effective_message.reply_text('Please input text')
        return  # Reenter current state until valid user input

    return READ_TIME_SELECTION


def read_time_selection_from_button(bot, update, chat_data, job_queue):
    if not chat_data:
        logger.error(f"No chat data/user_data available to set reminder. Chat: {chat_data}. Update: {update.to_dict()}")
        update.callback_query.message.reply_text("I'm sorry, I forgot who you are! let's try again ")
        return ConversationHandler.END

    logger.info(f"User time selection: {update.callback_query.data!r}")
    try:
        requested_delay = int(update.callback_query.data)
    except ValueError:
        logger.info(f"Received input from another message with inline buttons: {update.callback_query.data}")
        update.callback_query.message.edit_text('👻')
        return ConversationHandler.END

    if requested_delay == CUSTOM:
        logger.info("User selected custom date. Replying with available formats..")
        text = (f"» *When should i remind you?*\n"
                f"I understand dates like:\n"
                f"👉 in 45 minutes\n"
                f"👉 today at 17:00\n"
                f"👉 tomorrow at 13:00\n"
                f"👉 on friday at 21:00\n"
                f"👉 d/m hh:mm\n"
                )
        update.callback_query.message.edit_text(
            text=text,
            reply_markup=None,
            parse_mode='markdown'
        )
        logger.info("Waiting for user input on remind date")
        return READ_CUSTOM_DATE

    # Get datetime from requested_delay seconds
    when = datetime_from_answer(requested_delay)
    logger.info("Setting up new reminder from callback selection")
    chat_data.update({'remind_date_iso': when.isoformat()})
    job_context = copy.deepcopy(chat_data)

    _setup_reminder_and_reply(bot, update, job_context, job_queue, when, from_callback=True)

    logger.info("Conversation ended successfully")
    return ConversationHandler.END


def read_custom_date(bot, update, chat_data, job_queue, user_data):
    """Parse offseted date from user and save a job in utc time. Show reminder details localized"""
    user_date = update.message.text
    user_offset = user_data.get('offset', 0)
    logger.info(f'User input date: {user_date}. Attempting parsing with offset: {user_offset}')

    date = dateparser.parse(
        update.message.text,
        settings={'PREFER_DATES_FROM': 'future',
                  'RELATIVE_BASE': user_current_time(user_offset)}
    )
    if date is None:
        logger.error('Error parsing date. Waiting for user retry.')
        update.message.reply_text('What date is that? 🤨\n'
                                  'Try again with a more standard format. i.e: `d/m hh:mm`',
                                  parse_mode='markdown')
        return

    utc_date = utc_time_from_user_date(date, user_offset)
    logger.info(f"Parsed local {date} into  UTC {utc_date}")
    logger.info("Setting up new reminder from custom date")

    chat_data.update({'remind_date_iso': utc_date.isoformat()})
    job_context = copy.deepcopy(chat_data)

    _setup_reminder_and_reply(bot, update, job_context, job_queue, utc_date)

    logger.info("Conversation ended successfully")
    return ConversationHandler.END


reminders_set = ConversationHandler(
    entry_points=[
        CommandHandler('r', remind, pass_args=True, pass_chat_data=True, pass_user_data=True),
        CommandHandler('remind', remind, pass_args=True, pass_chat_data=True, pass_user_data=True),
        CommandHandler('recordar', remind, pass_args=True, pass_chat_data=True, pass_user_data=True)
    ],
    states={
        READ_REMINDER: [
            # If user hasn't specified what to remind, wait until s/he writes it.
            MessageHandler(Filters.text, read_reminder, pass_chat_data=True, pass_user_data=True)
        ],
        READ_TIME_SELECTION: [
            # Wait for user input on when s/he wants to be reminded
            CallbackQueryHandler(
                read_time_selection_from_button,
                pass_chat_data=True,
                pass_job_queue=True,
            )
        ],
        READ_CUSTOM_DATE: [
            # If user selected Custom option, wait until it writes a date as remind time
            MessageHandler(Filters.text, read_custom_date,
                           pass_chat_data=True,
                           pass_job_queue=True,
                           pass_user_data=True,
                           )
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
    allow_reentry=True,
    name='Set Reminders',
    persistent=True
)