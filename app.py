import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from commands import command_start, command_set_emoji_set
from sender import resend_message, emoji_callback
from settings import BOT_TOKEN, database

logger = logging.getLogger(__name__)


def error(bot, update, e):
    del bot
    logger.warning('Update "%s" caused error "%s"' % (update, e))


def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    commands = [
        CommandHandler("start", command_start),
        CommandHandler("help", command_start),
        CommandHandler("emoji", command_set_emoji_set, pass_args=True),
        CallbackQueryHandler(emoji_callback),
    ]
    for command in commands:
        dp.add_handler(command)

    dp.add_handler(MessageHandler(Filters.all, resend_message))

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()
    database.close()


if __name__ == '__main__':
    main()
