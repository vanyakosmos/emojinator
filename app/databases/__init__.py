from typing import Dict

from telegram import Message, CallbackQuery, Chat, User

from .postgres import PostgresDatabase


class AbstractDB(object):
    def init_chat(self, chat: Chat):
        """
        Check if chat already in DB, if no then register chat and set up default reactions.
        """
        pass

    def add_message(self, message: Message, message_from: User, op: User):
        """
        Get current reactions for chat and set them to the message.
        """
        pass

    def rate(self, query: CallbackQuery) -> Dict[str, int]:
        """
        Get scores after rating the message using data obtained from query:
        chat_id, message_id, user_id and chosen emoji.
        """
        pass

    def set_emojis(self, chat_id, emojis: list):
        """
        Set specific emojis for chat and remove old ones.
        """
        pass

    def get_emojis(self, chat_id):
        """
        Get emojis from specified chat.
        """
        pass
