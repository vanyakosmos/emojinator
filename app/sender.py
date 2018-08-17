import logging
import re

from telegram import Bot, Message, Update

from .decorators import log
from .settings import database
from .utils import get_buttons_markup


logger = logging.getLogger(__name__)
link = re.compile(r'https?://.\S+')


@log
def resend_message(bot: Bot, update: Update):
    resent = True
    message: Message = update.message

    if emoji_reply(bot, message):
        return

    # ignore message if it starts with --
    text = message.text or message.caption
    if text and text.startswith('--'):
        return

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
        skip = all([
            not message.forward_from,
            not message.forward_from_chat,
            not link.findall(message.text),
            not message.text.startswith('++'),
        ])
        if skip:
            return
        if message.text.startswith('++'):
            message.text = message.text[2:]
        logger.debug('Resending text...')
        send_text(bot, message)
    else:
        resent = False

    if resent:
        message.delete()


def emoji_reply(bot: Bot, message: Message):
    bot_message = message.reply_to_message
    if not bot_message:
        return False
    text = message.text or message.caption
    if not text:
        return False

    text = text.strip()
    to_bot = bot_message.from_user.id == bot.get_me().id
    start_with_plus = text.startswith('+')
    short = 1 < len(text) <= 10
    if to_bot and start_with_plus and short:
        button = text[1:]
        database.add_button(bot_message, button)
        rates, _ = database.rate_message(bot_message.chat_id,
                                         bot_message.message_id,
                                         message.from_user,
                                         button)
        original_msg = database.original_message(chat_id=bot_message.chat_id,
                                                 msg_id=bot_message.message_id)
        reply_markup = get_buttons_markup(original_msg, rates)
        bot_message.edit_reply_markup(reply_markup=reply_markup)
        message.delete()
        return True
    return False


def send_media(message: Message, sender, file_type_id: dict):
    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(message, rates)

    sent_message = sender(chat_id=message.chat_id,
                          caption=message.caption_html,
                          reply_markup=reply_markup,
                          disable_notification=True,
                          parse_mode='HTML',
                          **file_type_id)
    database.add_message(sent_message, message.from_user,
                         message.forward_from, original_message=message)


def send_text(bot: Bot, message: Message):
    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(message, rates)
    sent_message = bot.send_message(text=message.text_html,
                                    chat_id=message.chat_id,
                                    reply_markup=reply_markup,
                                    disable_notification=True,
                                    parse_mode='HTML')
    database.add_message(sent_message, message.from_user,
                         message.forward_from_chat or message.forward_from,
                         original_message=message)
