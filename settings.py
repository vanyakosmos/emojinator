import os
import logging

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logging.basicConfig(format='%(asctime)s ~ %(levelname)-10s %(name)-25s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    level=logging.DEBUG)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('JobQueue').setLevel(logging.WARNING)


DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

BOT_TOKEN = os.getenv('BOT_TOKEN')
REDIS_URL = os.getenv('REDIS_URL')

# heroku
APP_NAME = os.getenv('APP_NAME')
PORT = os.getenv('PORT')
