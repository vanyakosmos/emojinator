import logging

from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

from app.commands import command_start, command_set_up_buttons
from app.sender import resend_message, button_callback
from app.settings import database
from app.env_vars import DEBUG, BOT_TOKEN, PORT, APP_NAME

logger = logging.getLogger(__name__)


def error(bot: Bot, update: Update, e):
    del bot
    if str(e) == "Message can't be deleted":
        logger.warning(f"Can't delete message from user: {update.message.from_user}")
    else:
        logger.warning('Update "%s" caused error "%s"' % (update, e))


def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    commands = [
        CommandHandler("start", command_start),
        CommandHandler("help", command_start),
        CommandHandler("setup", command_set_up_buttons, pass_args=True),
        CallbackQueryHandler(button_callback),
    ]
    [dp.add_handler(c) for c in commands]

    dp.add_handler(MessageHandler(Filters.all, resend_message))
    dp.add_error_handler(error)

    if DEBUG:
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN)
        updater.bot.set_webhook(f"https://{APP_NAME}.herokuapp.com/{BOT_TOKEN}")
    updater.idle()
    database.close()


if __name__ == '__main__':
    main()
