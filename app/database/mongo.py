import logging
from typing import Dict, List

import pymongo
from pymongo import ReturnDocument
from telegram import CallbackQuery, Chat, Message, User

from app.env_vars import MONGODB_URI
from . import serializers


# todo: optimize queries with bulk operations
class MongoDB(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = pymongo.MongoClient(MONGODB_URI)
        self.db = self.client.get_database()

        self.messages = self.db.get_collection('messages')
        self.users = self.db.get_collection('users')
        self.rates = self.db.get_collection('rates')
        self.chats = self.db.get_collection('chats')

    def add_message(self, message: Message, from_user: User, forward_from: User):
        # insert message
        # add new message
        rates = self.get_buttons_rates(message.chat)
        self.messages.insert_one(
            serializers.message(message, from_user, forward_from, rates)
        )
        # upsert users
        self._upsert_user(from_user)
        if forward_from:
            self._upsert_user(forward_from)

    def _upsert_user(self, user):
        self.users.update_one(
            {'user_id': user.id},
            {"$set": serializers.user(user)},
            upsert=True
        )

    def rate(self, query: CallbackQuery) -> Dict[str, int] or None:
        chat_id = query.message.chat_id
        msg_id = query.message.message_id
        user_id = query.from_user.id
        chosen = query.data

        # check if messages unregistered
        msg = self.messages.find_one({
            'chat_id': chat_id,
            'msg_id': msg_id,
        })
        if msg is None:
            self.logger.debug('Unregistered messages rated.')
            return None

        # update user info
        self._upsert_user(query.from_user)

        # delete old rate and check if clicked button was the same as previously clicked
        same, msg = self._delete_old_rate(chat_id, msg_id, user_id, chosen)

        if not same:
            msg = self._add_new_rate(chat_id, msg_id, user_id, chosen)

        return msg.get('rates')

    def _delete_old_rate(self, chat_id, msg_id, user_id, chosen):
        """
        :return: (is same button, updated message)
        """
        rate = self.rates.find_one_and_delete({
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
        self.rates.insert_one(
            serializers.rate(chat_id, msg_id, user_id, chosen)
        )
        return self._update_message_rating(chat_id, msg_id, chosen, increment=1)

    def _update_message_rating(self, chat_id, msg_id, chosen, increment):
        return self.messages.find_one_and_update(
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
        res = self.chats.find_one({'chat_id': chat.id})
        if res is None:
            self.chats.insert_one({
                'chat_id': chat.id,
                'buttons': default_buttons,
            })
            return self._format_buttons(default_buttons)
        return self._format_buttons(res.get('buttons'))

    def _format_buttons(self, buttons) -> Dict[str, Dict[str, int]]:
        return {b: {'pos': i, 'score': 0} for i, b in enumerate(buttons)}

    def set_buttons(self, chat: Chat, buttons: List[str]):
        # upsert chat info
        self.chats.update_one({'chat_id': chat.id},
                              {"$set": serializers.chat(chat.id, buttons)},
                              upsert=True)

    def close(self):
        self.client.close()
