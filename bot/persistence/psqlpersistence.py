import ast
import copy
import json
import logging
from collections import defaultdict

from telegram.ext import BasePersistence

from bot.persistence.db import PSQLDatabase as Database


logger = logging.getLogger('psqlpersistence')


class PSQLPersistence(BasePersistence):
    def __init__(self, db_name):
        super().__init__()
        self.database = Database(db_name)
        self._state = None
        self._chat_data = None
        self._user_data = None
        self._conv_data = None
        self._loaded_data = False

    def _load_state_from_db(self):
        """Querys the db and load bot state into memory"""
        logger.info("Loading state from db..")
        try:
            with self.database as db:
                db.query("SELECT info FROM state")
                state = db.fetchone()
                logger.info('State from db: \n%s', state)
                self._state = state[0] if state else {}
                self._chat_data = defaultdict(dict, self._remap_chat_keys(self._state.get('chat_data', {})))
                self._user_data = defaultdict(dict, self._remap_user_keys(self._state.get('user_data', {})))
                self._conv_data = self._remap_conv_keys(defaultdict(dict, self._state.get('conv_data', {})))
                self._loaded_data = True

        except Exception:
            logger.error('Error loading state from db', exc_info=True)
            self._chat_data, self._user_data, self._conv_data = defaultdict(dict), defaultdict(dict), defaultdict(dict)
            self._loaded_data = False

    @staticmethod
    def _remap_chat_keys(chat_data):
        """Transforms user_data user_id keys to ints as expected by handler.py on line 120"""
        return PSQLPersistence.key_mapper(int, chat_data)

    @staticmethod
    def _remap_user_keys(user_data):
        """Transforms user_data user_id keys to ints as expected by handler.py on line 120"""
        return PSQLPersistence.key_mapper(int, user_data)

    @staticmethod
    def _remap_conv_keys(all_conversations):
        """Restore json key tuples from jsonification.
            '(1, 2)' -> (1, 2). That is, str -> tuple
        """
        return PSQLPersistence.remap_nested_keys(ast.literal_eval, all_conversations)

    @staticmethod
    def _dump_conv_keys(all_conversations):
        """Dump conversations tuple keys so they can be stored as json.

        They are then remapped to the original tuples by ast.literal_eval
        so that (1, 2) -> '(1, 2)'. That is, tuple -> str

        """
        return PSQLPersistence.remap_nested_keys(str, all_conversations)

    @staticmethod
    def remap_nested_keys(remap_func, nested_iterable):
        remapped_iterable = copy.deepcopy(nested_iterable)
        for conv_name, conversations in nested_iterable.items():
            remapped_iterable[conv_name] = PSQLPersistence.key_mapper(remap_func, conversations)

        return remapped_iterable

    @staticmethod
    def key_mapper(map_func, iterable):
        return {
            map_func(k): v
            for k, v in iterable.items()
        }

    def get_user_data(self):
        if not self._loaded_data:
            self._load_state_from_db()

        logger.info(f'User Data: {self._user_data}')
        return copy.deepcopy(self._user_data)

    def get_chat_data(self):
        if not self._loaded_data:
            self._load_state_from_db()

        logger.info(f'Chat Data: {self._chat_data}')
        return copy.deepcopy(self._chat_data)

    def get_conversations(self, name):
        logger.info(f"Getting '{name}' conversation..")
        if not self._loaded_data:
            self._load_state_from_db()

        conversation = self._conv_data.get(name, {})
        logger.info(f"'{name}' data: {conversation}")
        return copy.deepcopy(conversation)

    def update_conversation(self, name, key, new_state):
        """Will be called when a :attr:`telegram.ext.ConversationHandler.update_state`
        is called. this allows the storeage of the new state in the persistence.

        Args:
            name (:obj:`str`): The handlers name.
            key (:obj:`tuple`): The key of the conversation to be updated.
            new_state (:obj:`tuple` | :obj:`any`): The new state for the given key.
        """
        # map ints to strings to allow json dumping
        if self._conv_data.setdefault(name, {}).get(key) == new_state:
            return
        self._conv_data[name][key] = new_state

    def update_user_data(self, user_id, data):
        """Will be called by the :class:`telegram.ext.Dispatcher` after a handler has
        handled an update.

        Args:
            user_id (:obj:`int`): The user the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.dispatcher.user_data`[user_id].
        """
        user_id_str = str(user_id)
        if self._user_data.get(user_id_str) == data:
            return
        self._user_data[user_id_str] = data

    def update_chat_data(self, chat_id, data):
        """Will be called by the :class:`telegram.ext.Dispatcher` after a handler has
        handled an update.

        Args:
            chat_id (:obj:`int`): The chat the data might have been changed for.
            data (:obj:`dict`): The :attr:`telegram.ext.dispatcher.chat_data`[user_id].
        """
        chat_id_str = str(chat_id)
        if self._chat_data.get(chat_id_str) == data:
            return
        self._chat_data[chat_id_str] = data

    def _dump_state_to_json(self):
        state = {
            'chat_data': self._chat_data,
            'user_data': self._user_data,
            'conv_data': PSQLPersistence._dump_conv_keys(self._conv_data),
        }
        logger.info('Dumping %s', state)

        return json.dumps(state)

    def flush(self):
        """Be sure to dump latest data before bot shutdown"""
        logger.info('Saving bot state before shutdown..')
        with self.database as db:
            try:
                db.query("DELETE FROM state")
                db.query("INSERT INTO state (info) VALUES ('%s')" % self._dump_state_to_json())
            except Exception:
                logger.exception("Error saving bot state. Bot will not remember latest interactions")
            else:
                logger.info('SUCCESS. Bot state saved into db')

        logger.info('Closing database..')
        self.database.close()