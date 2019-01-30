import logging
import os
import random
from datetime import datetime, timedelta

import dateparser
import pytz

from bot.keyboard import done_or_repeat_reminder, time_options_keyboard
from bot.persistence.db_ops import add_reminder, expire_reminder
from bot.persistence.models import Reminder

logger = logging.getLogger(__name__)


def _tag_user(user):
    if user.username:
        return f'@{user.username}'
    else:
        return f"[{user.first_name}](tg://user?id={user.id})"


def init_reminder_context(to_remind, user, chat_id):
    logger.info(f"Building reminder context for {user.name}")
    return {
        'thing_to_remind': to_remind,
        'user_id': user.id,
        'user_tag': _tag_user(user),
        'chat_id': chat_id,
    }


def msg_admin(bot, message, **kwargs):
    bot.send_message(chat_id=os.environ['ADMIN_ID'], text=message, **kwargs)


def datetime_from_answer(time_delay):
    """Returns a datetime object and its isoformat from time_delay in seconds"""
    when = datetime.now() + timedelta(seconds=time_delay)
    return when


def add_reminder_job(bot, update, job_queue, job_context, when):
    logger.info(f"Adding job to db..")
    added = add_job_to_db(job_context)
    if added:
        job_queue.run_once(send_notification, when, context=job_context)
        logger.info(f"Job added to job queue and db.")
    else:
        logger.error('Could not save reminder job')
        msg_admin(bot, f"Error saving reminder.\n CONTEXT:\n{job_context}\n")

    return added


def add_job_to_db(job_context: dict) -> bool:
    """Saves a reminder in db based on the job_context"""
    try:
        reminder = Reminder(
            text=job_context['thing_to_remind'],
            user_id=job_context['user_id'],
            user_tag=job_context['user_tag'],
            remind_time=job_context['remind_date_iso'],
            chat_id=job_context['chat_id'],
            job_context=job_context,
            key=reminder_key(job_context)
        )
        add_reminder(reminder)
        return True
    except KeyError:
        logger.exception('Job context keys not properly initialized.')
        return False
    except Exception:
        logger.exception("Error saving reminder to db.")
        return False


def reminder_key(job_ctx):
    return '>'.join(
        (str(job_ctx['user_id']), job_ctx['thing_to_remind'], job_ctx['remind_date_iso'])
    )


def send_notification(bot, job):
    TIME_ICONS = ['⏰', '🔊', '🔈', '🔉', '📣', '📢', '❕', '🎉', '🎊', '⏱']
    random_time_emoji = random.choice(TIME_ICONS)
    to_remind = job.context['thing_to_remind']

    bot.send_message(
        chat_id=job.context['chat_id'],
        text=f"{job.context['user_tag']} {to_remind} {random_time_emoji} ",
        reply_markup=done_or_repeat_reminder()
    )
    logger.info(f"Reminded {job.context['user_tag']} of {to_remind}")

    expire_reminder(reminder_key(job.context))


def _show_time_options(update, from_remind_again=False):
    """Show user time options for when to be reminded."""
    message = {
        'text': 'Perfecto👌 Ahora elegí cuando querés recordarlo. 🕙',
        'reply_markup': time_options_keyboard(),
        'parse_mode': 'markdown'
    }
    if from_remind_again:
        # from Done or Remind again, has reply_markup
        update.effective_message.edit_text(**message)
    else:
        # from normal /remind, last message was text
        update.effective_message.reply_text(**message)



def reply_reminder_details(update, job_context, from_callback=False):
    utc_date = dateparser.parse(job_context['remind_date_iso'])
    bs_as_date = pytz.timezone('America/Argentina/Buenos_Aires').localize(utc_date)
    text = (f"✅ Listo, te voy a recordar `{job_context['thing_to_remind']}`"
            f" el {bs_as_date.strftime('%d/%m')} a las {bs_as_date.strftime('%H:%M')} 🔔")
    if from_callback:
        update.callback_query.message.edit_text(
            text=text,
            reply_markup=None,
            parse_mode='markdown'
        )
    else:
        update.message.reply_text(text, parse_mode='markdown')


def isoformat_to_datetime(date_string):
    return dateparser.parse(date_string)
