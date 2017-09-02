import logging
from typing import Dict, List

import pymongo
from pymongo import ReturnDocument
from telegram import CallbackQuery, Chat, Message, User

from app.env_vars import MONGO_URL


def serialize_message(message: Message, from_user: User, forward_from: User, rates):
    return {
        'chat_id': message.chat_id,
        'msg_id': message.message_id,
        'from_user': from_user and from_user.id,
        'forward_from': forward_from and forward_from.id,
        'rates': rates,  # { button: {pos: int, score: int} }
    }


def serialize_user(user: User):
    return {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }


def serialize_chat(chat_id, buttons):
    return {
        'chat_id': chat_id,
        'buttons': buttons,
    }


def serialize_rate(chat_id, msg_id, user_id, chosen):
    return {
        'chat_id': chat_id,
        'msg_id': msg_id,
        'user_id': user_id,
        'chosen': chosen,
    }


class Cols(object):
    MESSAGES = 'messages'
    USERS = 'users'
    RATES = 'rates'
    CHAT = 'chats'


# todo: optimize queries with bulk operations
class MongoDB(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client.get_database('test')

    def add_message(self, message: Message, from_user: User, forward_from: User):
        # insert message
        # add new message
        rates = self.get_buttons_rates(message.chat)
        self.db.get_collection(Cols.MESSAGES).insert_one(
            serialize_message(message, from_user, forward_from, rates)
        )
        # upsert users
        self._upsert_user(from_user)
        if forward_from:
            self._upsert_user(forward_from)

    def _upsert_user(self, user):
        self.db.get_collection(Cols.USERS).update_one(
            {'user_id': user.id},
            {"$set": serialize_user(user)},
            upsert=True
        )

    def rate(self, query: CallbackQuery) -> Dict[str, int] or None:
        chat_id = query.message.chat_id
        msg_id = query.message.message_id
        user_id = query.from_user.id
        chosen = query.data

        # check if message unregistered
        msg = self.db.get_collection(Cols.MESSAGES).find_one({
            'chat_id': chat_id,
            'msg_id': msg_id,
        })
        if msg is None:
            self.logger.debug('Unregistered message rated.')
            return None

        same, msg = self._delete_old_rate(chat_id, msg_id, user_id, chosen)

        if not same:
            msg = self._add_new_rate(chat_id, msg_id, user_id, chosen)

        return msg.get('rates')

    def _delete_old_rate(self, chat_id, msg_id, user_id, chosen):
        """
        :return: (is same button, updated message)
        """
        rate = self.db.get_collection(Cols.RATES).find_one_and_delete({
            'chat_id': chat_id,
            'msg_id': msg_id,
            'user_id': user_id,
        })
        if rate:
            old_chosen = rate.get('chosen')
            msg = self._update_message_rating(chat_id, msg_id, old_chosen, increment=-1)
            return old_chosen == chosen, msg
        return False, None

    def _add_new_rate(self, chat_id, msg_id, user_id, chosen) -> dict:
        self.db.get_collection(Cols.RATES).insert_one(
            serialize_rate(chat_id, msg_id, user_id, chosen)
        )
        return self._update_message_rating(chat_id, msg_id, chosen, increment=1)

    def _update_message_rating(self, chat_id, msg_id, chosen, increment):
        return self.db.get_collection(Cols.MESSAGES).find_one_and_update(
            {
                'chat_id': chat_id,
                'msg_id': msg_id,
            },
            {
                '$inc': {f"rates.{chosen}.score": increment},
            },
            return_document=ReturnDocument.AFTER)

    def get_buttons_rates(self, chat: Chat) -> Dict[str, Dict[str, int]]:
        default_buttons = ['👍', '❤️', '😂', '😯', '😢', '😡']  # tnx facebook
        res = self.db.get_collection(Cols.CHAT).find_one({'chat_id': chat.id})
        if res is None:
            self.db.get_collection(Cols.CHAT).insert_one({
                'chat_id': chat.id,
                'buttons': default_buttons,
            })
            return self._format_buttons(default_buttons)
        return self._format_buttons(res.get('buttons'))

    def _format_buttons(self, buttons) -> Dict[str, Dict[str, int]]:
        return {b: {'pos': i, 'score': 0} for i, b in enumerate(buttons)}

    def set_buttons(self, chat: Chat, buttons: List[str]):
        # upsert chat info
        self.db.get_collection(Cols.CHAT).update_one({'chat_id': chat.id},
                                                     {"$set": serialize_chat(chat.id, buttons)},
                                                     upsert=True)

    def close(self):
        self.client.close()
