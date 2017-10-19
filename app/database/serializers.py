from telegram import Message, User


def message(msg: Message, from_user: User, forward_from: User, rates):
    return {
        'chat_id': msg.chat_id,
        'msg_id': msg.message_id,
        'from_user': from_user and from_user.id,
        'forward_from': forward_from and forward_from.id,
        'rates': rates,  # { button: {pos: int, score: int} }
    }


def user(usr: User):
    return {
        'user_id': usr.id,
        'username': usr.username,
        'first_name': usr.first_name,
        'last_name': usr.last_name,
    }


def chat(chat_id, buttons):
    return {
        'chat_id': chat_id,
        'buttons': buttons,
    }


def rate(chat_id, msg_id, user_id, chosen):
    return {
        'chat_id': chat_id,
        'msg_id': msg_id,
        'user_id': user_id,
        'chosen': chosen,
    }
