import logging
from typing import Dict

from telegram import Message, CallbackQuery, Chat, User

from . import AbstractDB


class EmojiMessage(object):
    def __init__(self, emojis):
        self._rating = {em: set() for em in emojis}

    @staticmethod
    def from_json(data: dict):
        """
        data::

            {
                emoji_1: [user_id_1, user_id_2],
                emoji_2: [user_id_3]
            }
        """
        message = EmojiMessage(list(data.keys()))
        for em, rate in data.items():
            message._rating[em] = set(rate)
        return message

    def to_json(self):
        data = {}
        for em, rate in self._rating.items():
            data[em] = list(data)
        return self._rating

    def rate(self, chosen_emoji, user_id):
        logging.debug(f'User {user_id} rate message with emoji: {chosen_emoji}')
        rated_emoji = None
        res = {}
        for em, users in self._rating.items():
            res[em] = len(users)
            if user_id in users:
                rated_emoji = em
        if rated_emoji != chosen_emoji:
            res[chosen_emoji] += 1
            self._rating[chosen_emoji].add(user_id)
        if rated_emoji:
            res[rated_emoji] -= 1
            self._rating[rated_emoji].remove(user_id)
        return res


class EmojiChat(object):
    def __init__(self, chat_id):
        self._id = chat_id
        self._emojis = ['👍', '👎']
        self._messages = {}

    @property
    def emojis(self):
        return list(self._emojis)

    @emojis.setter
    def emojis(self, emojis: list):
        self._emojis = emojis

    def add_message(self, message_id: int):
        logging.debug(f'Added message {message_id}')
        self._messages[message_id] = EmojiMessage(self.emojis)

    def get_message(self, message_id) -> EmojiMessage:
        return self._messages[message_id]


class Database(AbstractDB):
    def __init__(self):
        self.chats = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def init_chat(self, chat: Chat):
        """
        Registering chat in database.
        """
        self.logger.debug(f'Added chat: {chat.id}')
        if chat.id not in self.chats:
            self.chats[chat.id] = EmojiChat(chat.id)

    def rate(self, query: CallbackQuery) -> Dict[str, int]:
        """
        Get scores after rating the message using data obtained from query:
        chat_id, message_id, user_id and chosen emoji.
        """
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        user_id = query.from_user.id
        chosen_emoji = query.data
        self.logger.debug(f'Rating message: {message_id}, em: {chosen_emoji}')

        chat = self.chats[chat_id]
        message = chat.get_message(message_id)
        return message.rate(chosen_emoji, user_id)

    def add_message(self, message: Message, message_from: User, op: User):
        """
        Registering message with current emojis sat for chat.
        """
        self.chats[message.chat_id].add_message(message.message_id)

    def set_emojis(self, chat_id, emojis: list):
        """
        Set specific emojis for chat.
        """
        chat = self.chats[chat_id]
        chat.emojis = emojis

    def get_emojis(self, chat_id):
        """
        Get emojis from specified chat.
        """
        chat = self.chats[chat_id]
        return chat.emojis
