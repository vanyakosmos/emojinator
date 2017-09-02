import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/test')

# heroku
APP_NAME = os.getenv('APP_NAME')
PORT = int(os.getenv('PORT', '5000'))
