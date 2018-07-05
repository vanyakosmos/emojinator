import logging
from functools import wraps

from telegram import Bot, Update


def log(func):
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def new_func(*args, **kwargs):
        logger.debug('Called ::' + func.__name__)
        return func(*args, **kwargs)

    return new_func


def admin_access(func):
    @wraps(func)
    def new_func(bot: Bot, update: Update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id == update.message.chat.id:
            return func(bot, update, *args, **kwargs)
        admins = bot.get_chat_administrators(update.message.chat.id)
        admins_ids = {admin.user.id for admin in admins}
        if user_id in admins_ids:
            return func(bot, update, *args, **kwargs)

    return new_func
