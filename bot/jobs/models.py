import os
import json

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, VARCHAR

Base = declarative_base()

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)


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
