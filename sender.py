import logging

from telegram import Bot, Update, Message, InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

emojis = {
    '👍': 0,
    '👎': 0,
    '😡': 0
}


def resend_message(bot: Bot, update: Update):
    message: Message = update.message
    user = message.from_user
    if user.last_name:
        by_user = f'by {user.first_name} {user.last_name} (@{user.username})'
    else:
        by_user = f'by {user.first_name} (@{user.username})'

    if message.photo:
        logger.debug('Resending photo...')
        send_media(message, by_user,
                   bot.send_photo,
                   {'photo': message.photo[0].file_id})
    elif message.video:
        logger.debug('Resending video...')
        send_media(message, by_user,
                   bot.send_video,
                   {'video': message.video.file_id})
    elif message.document:
        logger.debug('Resending document...')
        send_media(message, by_user,
                   bot.send_document,
                   {'document': message.document.file_id})
    elif message.text:
        logger.debug('Resending text...')
        message.reply_text("text")


def get_emoji_markup():
    keyboard = []
    for e, count in emojis.items():
        text = e
        if count:
            text += f' {count}'
        keyboard.append(InlineKeyboardButton(text, callback_data='poll:' + e))

    return InlineKeyboardMarkup([keyboard])


def send_media(message: Message, by_user: str, send_media_func, file_type_id: dict):
    if message.caption:
        caption = message.caption + '\n' + by_user  # fixme: caption size 0-200
    else:
        caption = by_user

    reply_markup = get_emoji_markup()

    send_media_func(chat_id=message.chat_id,
                    caption=caption[:200],
                    reply_markup=reply_markup,
                    **file_type_id)
