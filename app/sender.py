import logging
import re

from telegram import Bot, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.constants import MAX_CAPTION_LENGTH

from .decorators import log
from .settings import database

logger = logging.getLogger(__name__)
link = re.compile(r'https?://.\S+')


@log
def resend_message(bot: Bot, update: Update):
    message: Message = update.message
    database.init_chat(message.chat)

    if message.reply_to_message:
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
        if (not message.forward_from and
                not message.forward_from_chat and
                not link.findall(message.text)):
            return

        logger.debug('Resending text...')
        send_text(bot, message)

    message.delete()


def button_callback(bot: Bot, update: Update):
    query = update.callback_query
    message = query.message
    res = database.rate(query)
    if res:
        reply_markup = get_buttons_markup(res)
        bot.edit_message_reply_markup(chat_id=message.chat_id,
                                      message_id=message.message_id,
                                      reply_markup=reply_markup)


def get_buttons_markup(buttons: dict):
    keys = []
    sorted_bs = sorted(buttons.keys())
    for name in sorted_bs:
        text = name
        count = buttons[name]
        if count:
            text += f' {count}'
        keys.append(InlineKeyboardButton(text, callback_data=name))
    max_cols = 3
    keyboard = []
    while keys:
        keyboard += [keys[:max_cols]]
        keys = keys[max_cols:]
    return InlineKeyboardMarkup(keyboard)


def full_name(user: User):
    names = [n for n in [user.first_name, user.last_name]
             if n is not None]
    return ' '.join(names)


def authors_text(message: Message):
    if message.from_user.username:
        text = 'by @' + message.from_user.username
    else:
        text = 'by ' + full_name(message.from_user)

    if message.forward_from and message.from_user.username != message.forward_from.username:
        if message.forward_from.username:
            text += ', from @' + message.forward_from.username
        else:
            text += ', from ' + full_name(message.forward_from)

    if message.forward_from_chat:
        if message.forward_from_chat.username:
            text += ', from @' + message.forward_from_chat.username

    if message.caption:
        text = message.caption + '\n' + text
    if message.text:
        text = message.text + '\n' + text
    return text


def send_media(message: Message, sender, file_type_id: dict):
    caption = authors_text(message)

    buttons = {b: 0 for b in database.get_emojis(message.chat_id)}
    reply_markup = get_buttons_markup(buttons)
    sent_message = sender(chat_id=message.chat_id,
                          caption=caption[:MAX_CAPTION_LENGTH],
                          reply_markup=reply_markup,
                          **file_type_id)
    database.add_message(sent_message, message.from_user, message.forward_from)


def send_text(bot: Bot, message: Message):
    text = authors_text(message)

    buttons = {b: 0 for b in database.get_emojis(message.chat_id)}
    reply_markup = get_buttons_markup(buttons)
    sent_message = bot.send_message(text=text,
                                    chat_id=message.chat_id,
                                    reply_markup=reply_markup)
    database.add_message(sent_message, message.from_user, message.forward_from_chat or message.forward_from)
