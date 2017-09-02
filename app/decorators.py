import logging
from functools import wraps


def log(func):
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    def new_func(*args, **kwargs):
        logger.debug('Called ::' + func.__name__)
        return func(*args, **kwargs)

    return new_func
