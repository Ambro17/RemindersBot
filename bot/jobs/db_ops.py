import logging

from bot.jobs.models import Session, Reminder

logger = logging.getLogger(__name__)


def add_reminder(reminder):
    session = Session()
    session.add(reminder)
    session.commit()


def expire_reminder(key):
    session = Session()
    reminder = session.query(Reminder).filter_by(key=key).first()
    if reminder is None:
        logger.info(f"Reminder {key!r} does not exist on db")
        expired = False
    else:
        reminder.expired = True
        session.commit()
        logger.info(f"Reminder {key!r} Expired")
        expired = True

    return expired


def remove_reminder(text, **kwargs):
    session = Session()
    reminder = session.query(Reminder).filter_by(text=text, **kwargs).first()
    if reminder is None:
        logger.info(f"Reminder {text} does not exist on db")
        msg = f'🚫 El reminder `{text}` no existe en la base de datos'
    else:
        session.delete(reminder)
        logger.info(f"Reminder {text!r} DELETED")
        msg = f'✅ Reminder `{text}` borrado con éxito'

    session.commit()
    return msg


def get_reminders(**kwargs):
    session = Session()
    return session.query(Reminder).filter_by(**kwargs)
