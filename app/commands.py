from typing import List

from telegram import Bot, ParseMode, Update

from .decorators import admin_access, log
from .settings import database
from .utils import get_buttons_markup


@log
@admin_access
def command_start(bot: Bot, update: Update):
    del bot
    lines = [
        "This bot will automagically add polling panel to your images/gifs/videos/links.",
        "`/start` or `/help` - print this message",
        "`/setup <button> [<button>]*` - set up buttons"
    ]
    update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN)


@log
@admin_access
def command_set_up_buttons(bot: Bot, update: Update, args: List[str]):
    del bot
    chat = update.message.chat

    if not args:
        buttons = database.get_buttons_rates(chat)
        buttons = format_buttons(buttons.keys())
        text = f'Specify name for at least one button. Separate buttons names with space.\n' \
               f'Current buttons:\n' \
               f'{buttons}'
        update.message.reply_text(text)
    else:
        database.set_buttons(chat, args)
        bs = format_buttons(args)
        update.message.reply_text(f'New buttons: ' + bs)


def format_buttons(buttons: iter):
    return ' '.join(['[ ' + b + ' ]' for b in buttons])


def button_callback(bot: Bot, update: Update):
    query = update.callback_query
    message = query.message
    res = database.rate(query)
    if res:
        original_msg = database.original_message(query=query)
        reply_markup = get_buttons_markup(original_msg, res)
        bot.edit_message_reply_markup(chat_id=message.chat_id,
                                      message_id=message.message_id,
                                      reply_markup=reply_markup)
