import logging

from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup


logger = logging.getLogger(__name__)
file_types = {
    'photo': False,
    'doc/gif': False,
    'video': False,
    'link in text': False
}


def command_start(bot: Bot, update: Update):
    lines = ["This bot will automagically add emoji panel to your images.",
             "",
             "/start or /help - print this message",
             "/file - choosing file types",
             "/emoji - choose emojis"]
    bot.send_message(chat_id=update.message.chat_id,
                     text='\n'.join(lines))


def command_set_emoji_set(bot: Bot, update: Update):
    del bot, update


def get_file_markup():
    keyboard = []
    for t, c in file_types.items():
        mark = '✅' if c else '❌'
        keyboard.append([InlineKeyboardButton(f'{mark} {t}', callback_data='file:'+t)])

    return InlineKeyboardMarkup(keyboard)


def command_set_file_types(bot: Bot, update: Update):
    del bot
    reply_markup = get_file_markup()

    update.message.reply_text(text='Choose file types for emojification:',
                              reply_markup=reply_markup)
