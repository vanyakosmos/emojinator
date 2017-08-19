import logging

from telegram import Bot, Update

from settings import database


logger = logging.getLogger(__name__)


def command_start(bot: Bot, update: Update):
    chat = update.message.chat
    lines = ["This bot will automagically add emoji panel to your images/gifs/videos.",
             "",
             "/start or /help - print this message",
             "/emoji - set up emojis"]

    database.init_chat(chat=chat)
    bot.send_message(chat_id=chat.id,
                     text='\n'.join(lines))


def command_set_emoji_set(bot: Bot, update: Update, args: list):
    del bot
    chat = update.message.chat
    database.init_chat(chat=chat)
    if not args:
        update.message.reply_text('No emojis specified.')
    else:
        # todo: add only string with emojis
        database.set_emojis(chat_id=chat.id, emojis=args)
        update.message.reply_text(f'Customized emojis: {args}')
