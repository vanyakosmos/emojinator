from telegram import Message, User


class Serializer(object):
    @staticmethod
    def message(message: Message, from_user: User, forward_from: User, rates):
        return {
            'chat_id': message.chat_id,
            'msg_id': message.message_id,
            'from_user': from_user and from_user.id,
            'forward_from': forward_from and forward_from.id,
            'rates': rates,  # { button: {pos: int, score: int} }
        }

    @staticmethod
    def user(user: User):
        return {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

    @staticmethod
    def chat(chat_id, buttons):
        return {
            'chat_id': chat_id,
            'buttons': buttons,
        }

    @staticmethod
    def rate(chat_id, msg_id, user_id, chosen):
        return {
            'chat_id': chat_id,
            'msg_id': msg_id,
            'user_id': user_id,
            'chosen': chosen,
        }
