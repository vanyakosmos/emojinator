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

    if message.reply_to_message:
        if message.reply_to_message.from_user.id == bot.get_me().id \
                and message.text.strip().startswith('+') \
                and 1 < len(message.text.strip()) < 6:

            button = message.text.strip()[1:]
            rates = message.reply_to_message.get('rates')
            if button in rates.keys:
                return
            chosen = len(rates)
            rates[button] = {'pos': chosen, 'score': 0}

            reply_markup = get_buttons_markup(message.reply_to_message, rates)
            message.reply_to_message.edit_reply_markup(reply_markup)

            database.rate_message(message.reply_to_message.chat_id,
                                  message.reply_to_message.message_id,
                                  message.reply_to_message.from_user,
                                  chosen)
            message.delete()

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
    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(message, rates)

    sent_message = sender(chat_id=message.chat_id,
                          caption=message.caption,
                          reply_markup=reply_markup,
                          disable_notification=True,
                          **file_type_id)
    database.add_message(sent_message, message.from_user,
                         message.forward_from, original_message=message)


def send_text(bot: Bot, message: Message):
    rates = database.get_buttons_rates(message.chat)
    reply_markup = get_buttons_markup(message, rates)
    sent_message = bot.send_message(text=message.text,
                                    chat_id=message.chat_id,
                                    reply_markup=reply_markup,
                                    disable_notification=True)
    database.add_message(sent_message, message.from_user,
                         message.forward_from_chat or message.forward_from, original_message=message)
