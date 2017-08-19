import re
import logging

from telegram import Bot, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, User, TelegramError

from settings import database


logger = logging.getLogger(__name__)
link = re.compile(r'https?://.\S+')


def resend_message(bot: Bot, update: Update):
    message: Message = update.message
    database.init_chat(message.chat)

    if message.forward_from and message.forward_from.username == 'dummy2105_bot':
        return

    if message.photo:
        logger.debug('Resending photo...')
        send_media(message,
                   bot.send_photo,
                   {'photo': message.photo[0].file_id})
    elif message.video:
        logger.debug('Resending video...')
        send_media(message,
                   bot.send_video,
                   {'video': message.video.file_id})
    elif message.document:
        logger.debug('Resending document...')
        send_media(message,
                   bot.send_document,
                   {'document': message.document.file_id})
    elif message.text:
        logger.debug('Resending text...')
        send_text(bot, message)


def get_emoji_markup(emojis):
    keys = []
    sorted_ems = sorted(emojis.keys())
    for e in sorted_ems:
        text = e
        count = emojis[e]
        if count:
            text += f' {count}'
        keys.append(InlineKeyboardButton(text, callback_data=e))
    max_cols = 3
    keyboard = []
    while keys:
        keyboard += [keys[:max_cols]]
        keys = keys[max_cols:]
    return InlineKeyboardMarkup(keyboard)


def emoji_callback(bot: Bot, update: Update):
    query = update.callback_query
    message = query.message
    res = database.rate(query)
    if res:
        reply_markup = get_emoji_markup(res)
        bot.edit_message_reply_markup(chat_id=message.chat_id,
                                      message_id=message.message_id,
                                      reply_markup=reply_markup)


def full_name(user: User):
    ln = ' ' + user.last_name if user.last_name else ''
    return user.first_name + ln


def add_author(message: Message):
    if message.from_user.username:
        text = f'🌚 by @{message.from_user.username}'
    else:
        text = f'🌚 by {full_name(message.from_user)}'

    if message.forward_from and message.from_user.username != message.forward_from.username:
        if message.forward_from.username:
            text += f', from @{message.forward_from.username}'
        else:
            text += f', from {full_name(message.forward_from)}'

    if message.forward_from_chat:
        if message.forward_from_chat.username:
            text += f', from @{message.forward_from_chat.username}'

    if message.caption:
        text = message.caption + '\n' + text
    if message.text:
        text = message.text + '\n' + text
    return text


def send_media(message: Message, send_media_func, file_type_id: dict):
    caption = add_author(message)

    emojis = {em: 0 for em in database.get_emojis(message.chat_id)}
    reply_markup = get_emoji_markup(emojis)
    sent_message = send_media_func(chat_id=message.chat_id,
                                   caption=caption[:200],  # fixme: caption size 0-200
                                   reply_markup=reply_markup,
                                   **file_type_id)
    database.add_message(sent_message, message.from_user, message.forward_from)
    message.delete()


def send_text(bot: Bot, message: Message):
    if not link.findall(message.text) and not (message.forward_from or message.forward_from_chat):
        return

    text = add_author(message)

    emojis = {em: 0 for em in database.get_emojis(message.chat_id)}
    reply_markup = get_emoji_markup(emojis)
    sent_message = bot.send_message(text=text,
                                    chat_id=message.chat_id,
                                    reply_markup=reply_markup)
    database.add_message(sent_message, message.from_user, message.forward_from_chat or message.forward_from)
    message.delete()
