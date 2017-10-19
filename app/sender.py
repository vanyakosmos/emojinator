import logging
import re

from telegram import Bot, Chat, Message, Update, User
from telegram.constants import MAX_CAPTION_LENGTH

from .decorators import log
from .settings import database
from .utils import get_buttons_markup

logger = logging.getLogger(__name__)
link = re.compile(r'https?://.\S+')


@log
def resend_message(bot: Bot, update: Update):
    resent = True
    message: Message = update.message

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
    else:
        resent = False

    if resent:
        message.delete()


def send_media(message: Message, sender, file_type_id: dict):
    caption = signature_text(message)

    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(rates)
    sent_message = sender(chat_id=message.chat_id,
                          caption=caption[:MAX_CAPTION_LENGTH],
                          reply_markup=reply_markup,
                          disable_notification=True,
                          **file_type_id)


def signature_text(message: Message):
    from_user: User = message.from_user
    forward_from: User = message.forward_from
    forward_from_chat: Chat = message.forward_from_chat

    text = 'by ' + from_user.name

    if forward_from and from_user.name != forward_from.name:
        text += ', from ' + forward_from.name

    if forward_from_chat and forward_from_chat.username:
        text += ', from @' + forward_from_chat.username

    if message.caption:
        text = message.caption + '\n' + text
    if message.text:
        text = message.text + '\n' + text
    return text
    database.add_message(sent_message, message.from_user,
                         message.forward_from, original_message=message)


def send_text(bot: Bot, message: Message):
    text = signature_text(message)

    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(rates)
    sent_message = bot.send_message(text=text,
                                    chat_id=message.chat_id,
                                    reply_markup=reply_markup,
                                    disable_notification=True)
    database.add_message(sent_message, message.from_user,
                         message.forward_from_chat or message.forward_from, original_message=message)
