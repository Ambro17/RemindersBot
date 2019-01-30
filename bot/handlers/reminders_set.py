"""
    Handler that manages creation of new reminders
"""
import copy
import logging

import dateparser
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

from bot.constants import READ_REMINDER, READ_TIME_SELECTION, READ_CUSTOM_TIME, CUSTOM
from bot.utils import init_reminder_context, datetime_from_answer, add_reminder_job, reply_reminder_details, \
    _show_time_options

logger = logging.getLogger(__name__)


def remind(bot, update, args, chat_data):
    """Initialize reminder context and ask for reminder if it isn't yet known"""
    logger.info('STARTED new /remind conversation')
    if not args:
        # If the user did not specify what to remind, ask him/her
        update.effective_message.reply_text("⏰ Qué querés recordar?", quote=False)
        logger.info("Waiting for user input on what to remind..")
        return READ_REMINDER

    msg = update.message
    thing_to_remind = ' '.join(args)
    logger.info(f'Reminder args: {thing_to_remind}')

    context = init_reminder_context(thing_to_remind, msg.from_user, msg.chat_id)
    chat_data.update(context)
    logger.info(f"Read '{thing_to_remind}' from {context['user_tag']}."
                f" Offering time options..")

    # User time selection will be captured by read_time_selection_from_button
    logger.info('Showing time options..')
    _show_time_options(update)
    return READ_TIME_SELECTION


def read_reminder(bot, update, chat_data):
    try:
        msg = update.message
        logger.info(f'Read user input: {msg.text}')
        context = init_reminder_context(msg.text, msg.from_user, msg.chat_id)
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
        logger.error(f"No chat data available to set reminder. Update: {update.to_dict()}")
        update.callback_query.message.reply_text('I forgot who you are!')
        return ConversationHandler.END

    logger.info(f"User time selection: {update.callback_query.data!r}")
    requested_delay = int(update.callback_query.data)

    if requested_delay == CUSTOM:
        logger.info("User selected custom date. Replying with available formats..")
        text = (f"Ingresá cuando te debo recordar.\n"
                f"Entiendo fechas como:\n"
                f"👉 d/m hh:mm\n"
                f"👉 mañana a las 13:00\n"
                f"👉 viernes a las 21:00")
        update.callback_query.message.edit_text(
            text=text,
            reply_markup=None,
            parse_mode='markdown'
        )
        logger.info("Waiting for user input on remind date")
        return READ_CUSTOM_TIME

    # Get datetime from requested_delay seconds
    when = datetime_from_answer(requested_delay)
    logger.info("Setting up new reminder from callback selection")
    _setup_reminder(bot, update, chat_data, job_queue, when, from_callback=True)

    logger.info("Conversation ended successfully")
    return ConversationHandler.END


def _setup_reminder(bot, update, chat_data, job_queue, when, from_callback=False):
    """Setup a new reminder in the job_queue.

    Notify the user in chat_data the thing s/he wants to remind when *when* datetime
    occurs, by setting up a new run_once job on the job_queue
    """
    chat_data.update({'remind_date_iso': when.isoformat()})
    job_context = copy.deepcopy(chat_data)

    logger.info(f'Adding job to db an job queue with context: {job_context}')
    success = add_reminder_job(bot, update, job_queue, job_context, when)
    if success:
        logger.info('SUCCESS')
        reply_reminder_details(update, job_context, from_callback=from_callback)
    else:
        logger.error("ERROR. Could not save reminder.")
        update.callback_query.message.edit_text(
            text=f"🚫 Error guardando el reminder. Intentá de nuevo más tarde",
            reply_markup=None
        )


def parse_time_from_text(bot, update, chat_data, job_queue):
    # Update show_time_options keyboard
    user_date = update.message.text
    logger.info(f'User input date: {user_date}. Attempting parsing..')

    date = dateparser.parse(update.message.text, settings={'PREFER_DATES_FROM': 'future'})
    if date is None:
        logger.error('Error parsing date. Waiting for user retry.')
        update.message.reply_text('No pude interpretar la fecha.'
                                  ' Intenta de nuevo con un formato más estándar (`d/m hh:mm`)',
                                  parse_mode='markdown')
        return
    logger.info(f'Parsed user date: {date}')

    # Get datetime from input text
    when, when_iso = date, date.isoformat()
    logger.info("Setting up new reminder from custom date")
    _setup_reminder(bot, update, chat_data, job_queue, when)

    logger.info("Conversation ended successfully")
    return ConversationHandler.END


reminders_set = ConversationHandler(
    entry_points=[
        CommandHandler('r', remind, pass_args=True, pass_chat_data=True),
        CommandHandler('remind', remind, pass_args=True, pass_chat_data=True),
        CommandHandler('recordar', remind, pass_args=True, pass_chat_data=True)
    ],
    states={
        READ_REMINDER: [
            # If user hasn't specified what to remind, wait until s/he writes it.
            MessageHandler(Filters.text, read_reminder, pass_chat_data=True)
        ],
        READ_TIME_SELECTION: [
            # Wait for user input on when s/he wants to be reminded
            CallbackQueryHandler(
                read_time_selection_from_button,
                pass_chat_data=True,
                pass_job_queue=True
            )
        ],
        READ_CUSTOM_TIME: [
            # If user selected Custom option, wait until it writes a date as remind time
            MessageHandler(Filters.text, parse_time_from_text,
                           pass_chat_data=True,
                           pass_job_queue=True)
        ]
    },
    fallbacks=[],
    allow_reentry=True
)
