import logging

from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from settings import BOT_TOKEN
from sender import resend_message, get_emoji_markup, emojis
from commands import command_start, command_set_emoji_set, command_set_file_types, file_types, get_file_markup

logger = logging.getLogger(__name__)


def callback_file(bot: Bot, update: Update):
    query = update.callback_query
    typ, data = query.data.split(':')
    if typ == 'poll':
        emojis[data] += 1
        reply_markup = get_emoji_markup()
        bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      reply_markup=reply_markup)
    elif typ == 'file':
        file_types[data] = not file_types[data]

        reply_markup = get_file_markup()
        bot.edit_message_reply_markup(chat_id=query.message.chat_id,
                                      message_id=query.message.message_id,
                                      reply_markup=reply_markup)


def error(bot, update, e):
    del bot
    logger.warning('Update "%s" caused error "%s"' % (update, e))


def main():
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    commands = [
        CommandHandler("start", command_start),
        CommandHandler("help", command_start),
        CommandHandler("emoji", command_set_emoji_set),
        CommandHandler("file", command_set_file_types),
        CallbackQueryHandler(callback_file),
    ]
    for command in commands:
        dp.add_handler(command)

    dp.add_handler(MessageHandler(Filters.all, resend_message))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
