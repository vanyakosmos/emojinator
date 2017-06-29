import logging

from databases.ram import Database
from databases.postgres import PostgresDatabase

from env_conts import *

if DEBUG:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO

logging.basicConfig(format='%(asctime)s ~ %(levelname)-10s %(name)-25s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    level=logging_level)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('JobQueue').setLevel(logging.WARNING)

# database = Database()
database = PostgresDatabase()
