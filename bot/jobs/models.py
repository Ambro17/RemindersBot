import os
import json

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.dialects.postgresql import JSON

Base = declarative_base()

MINUTE = 60 # See https://community.fly.io/t/postgresql-connection-is-closed-error-after-a-few-minutes-of-activity/4768/3
engine = create_engine(os.environ['DATABASE_URL'], pool_recycle=30 * MINUTE)
Session = sessionmaker(bind=engine)


def create_tables():
    # Also manually CREATE TABLE state (info json); ALTER TABLE state OWNER TO remindersbot; not tracked by alchemy
    Base.metadata.create_all(engine)


class JSONEncodedValue(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class State(Base):
    __tablename__ = 'state'
    id = Column(Integer, primary_key=True)
    info = Column(JSON)

class Reminder(Base):
    __tablename__ = 'reminder'

    id = Column(Integer, primary_key=True)

    key = Column(String)
    text = Column(String)
    user_id = Column(String)
    user_tag = Column(String)
    remind_time = Column(String)
    chat_id = Column(String)
    offset = Column(Integer)
    expired = Column(Boolean, default=False)
    job_context = Column(JSONEncodedValue)

    def __repr__(self):
        return (f"Reminder(text={self.text}, user_id={self.user_id}, user_tag={self.user_tag},"
                f" remind_time={self.remind_time}, offset= {self.offset}, chat_id={self.chat_id},"
                f" key={self.key}, expired={self.expired})")


class Todo(Base):
    __tablename__ = 'todo'
    id = Column(Integer, primary_key=True)
    text = Column(String)
    done = Column(Boolean, default=False)
