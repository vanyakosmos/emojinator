from telegram import Bot, Update

from .decorators import log
from .settings import database


@log
def command_start(bot: Bot, update: Update):
    del bot
    chat = update.message.chat
    database.init_chat(chat=chat)
    lines = [
        "This bot will automagically add buttons panel for polling to your images/gifs/videos/links.",
        "/start or /help - print this message",
        "/setup - set up buttons"
    ]
    update.message.reply_text('\n'.join(lines))


@log
def command_set_up_buttons(bot: Bot, update: Update, args: list):
    del bot
    chat = update.message.chat
    database.init_chat(chat=chat)
    if not args:
        update.message.reply_text('Specify name for at least one button. Separate buttons with space.')
    else:
        database.set_emojis(chat_id=chat.id, emojis=args)
        bs = ' '.join(['[ ' + a + ' ]' for a in args])
        update.message.reply_text(f'New buttons: ' + bs)
