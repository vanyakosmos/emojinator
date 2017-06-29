import logging

from telegram import Bot, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup

from settings import database


logger = logging.getLogger(__name__)


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


def get_emoji_markup(emojis):
    keyboard = []
    for e, count in emojis.items():
        text = e
        if count:
            text += f' {count}'
        keyboard.append(InlineKeyboardButton(text, callback_data=e))
    return InlineKeyboardMarkup([keyboard])


def emoji_callback(bot: Bot, update: Update):
    query = update.callback_query
    message = query.message
    res = database.rate(query)
    reply_markup = get_emoji_markup(res)
    bot.edit_message_reply_markup(chat_id=message.chat_id,
                                  message_id=message.message_id,
                                  reply_markup=reply_markup)


def send_media(message: Message, send_media_func, file_type_id: dict):

    caption = f'by @{message.from_user.username}'
    if message.forward_from and message.from_user.username != message.forward_from.username:
        caption += f', from @{message.forward_from.username}'
    if message.forward_from_chat and message.from_user.username != message.forward_from_chat.username:
        caption += f', from @{message.forward_from_chat.username}'
    if message.caption:
        caption = message.caption + '\n' + caption  # fixme: caption size 0-200

    init_emojis = {em: 0 for em in database.get_emojis(message.chat_id)}
    reply_markup = get_emoji_markup(init_emojis)
    sent_message = send_media_func(chat_id=message.chat_id,
                                   caption=caption[:200],
                                   reply_markup=reply_markup,
                                   **file_type_id)
    database.add_message(sent_message)
    message.delete()
