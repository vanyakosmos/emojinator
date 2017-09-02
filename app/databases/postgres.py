import logging
from typing import Dict

import psycopg2 as psycopg2
from telegram import CallbackQuery, Chat, Message, User

from app.env_vars import DATABASE_URL
from . import AbstractDB


class PostgresDatabase(AbstractDB):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()

        # todo: check if tables already created and if no then do it (just do it)
        # self.drop_all_tables()
        # self.create_tables()

    def create_tables(self):
        self.cur.execute("CREATE TABLE users ("
                         "id BIGINT PRIMARY KEY, "
                         "fname varchar, "
                         "lname varchar, "
                         "username varchar);")

        self.cur.execute("CREATE TABLE chats ("
                         "id BIGINT PRIMARY KEY, "
                         "title varchar, "
                         "username varchar);")

        # fixme messages must have specified chat_id
        self.cur.execute("CREATE TABLE messages ("
                         "id BIGINT PRIMARY KEY, "
                         "from_user_id BIGINT REFERENCES users(id), "
                         "forwarded_from_id BIGINT REFERENCES users(id));")

        self.cur.execute("CREATE TABLE chat_reactions ("
                         "id SERIAL PRIMARY KEY, "
                         "chat_id BIGINT REFERENCES chats(id), "
                         "reaction VARCHAR);")

        self.cur.execute("CREATE TABLE reactions ("
                         "id SERIAL PRIMARY KEY, "
                         "chat_id BIGINT REFERENCES chats(id), "
                         "message_id BIGINT REFERENCES messages(id),"
                         "reaction VARCHAR,"
                         "count INTEGER);")

        self.cur.execute("CREATE TABLE rates ("
                         "id SERIAL PRIMARY KEY, "
                         "user_id BIGINT REFERENCES users(id),"
                         "reaction_id INTEGER REFERENCES reactions(id));")
        # check:
        # self.cur.execute("INSERT INTO users (id, fname, lname, username) VALUES (1, 'kek', 'cheburek', 'pshe')")
        # self.cur.execute("SELECT * FROM users;")
        # print(self.cur.fetchone())
        self.conn.commit()

    def drop_all_tables(self):
        self.cur.execute("DROP TABLE IF EXISTS users, chats, messages, chat_reactions, reactions, rates;")
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()

    def init_chat(self, chat: Chat):
        """
        Check if chat already in DB, if no then register chat and set up default reactions.
        """
        self.cur.execute("SELECT id FROM chats WHERE id=%(id)s;", {'id': chat.id})
        res = self.cur.fetchall()
        if res:
            self.logger.debug(f'Got chat {chat.id}')
            return

        self.cur.execute("INSERT INTO chats (id, title, username) VALUES "
                         "(%s, %s, %s)",
                         (chat.id, chat.title, chat.username))
        self.cur.execute("INSERT INTO chat_reactions (chat_id, reaction) VALUES "
                         "(%(chat_id)s, %(em1)s), (%(chat_id)s, %(em2)s)",
                         {'chat_id': chat.id, 'em1': '👍', 'em2': '👎'})
        self.conn.commit()

    def add_message(self, message: Message, message_from: User, op: User):
        """
        Get current reactions for chat and set them to the message.
        """
        self.add_user(message_from)
        self.add_user(op)

        self.cur.execute("SELECT reaction FROM chat_reactions WHERE chat_id=%(chat_id)s;",
                         {'chat_id': message.chat_id})
        reactions = self.cur.fetchall()  # [(emoji, )]
        self.cur.execute("INSERT INTO messages (id, from_user_id, forwarded_from_id) VALUES "
                         "(%s, %s, %s)",
                         (message.message_id, message_from.id, op.id if op else None))
        for reaction in reactions:
            emoji = reaction[0]
            self.cur.execute("INSERT INTO reactions (chat_id, message_id, reaction, count) VALUES "
                             "(%s, %s, %s, 0)",
                             (message.chat_id, message.message_id, emoji))
        self.conn.commit()

    def add_user(self, user: User):
        if not user:
            return
        self.cur.execute("SELECT * FROM users "
                         "WHERE id=%(user_id)s;",
                         {'user_id': user.id})
        user_data = self.cur.fetchone()
        if not user_data:
            self.cur.execute("INSERT INTO users (id, fname, lname, username) VALUES "
                             "(%(user_id)s, %(fname)s, %(lname)s, %(username)s)",
                             {'user_id': user.id,
                              'fname': user.first_name,
                              'lname': user.last_name,
                              'username': user.username})
            self.conn.commit()

    def rate(self, query: CallbackQuery) -> Dict[str, int]:
        """
        Get scores after rating the message using data obtained from query:
        chat_id, message_id, user_id and chosen emoji.
        """
        # todo: optimise database calls (?)
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        user_id = query.from_user.id
        chosen_emoji = query.data
        self.logger.debug(f'Rating message: {message_id}, em: {chosen_emoji}')

        # protect against the ability to rate messages that are not in database
        self.cur.execute("SELECT * FROM messages WHERE id=%(message_id)s;", {'message_id': message_id})
        mes = self.cur.fetchone()
        if not mes:
            return {}

        self.add_user(query.from_user)

        # get reactions for message
        self.cur.execute("SELECT id, reaction, count FROM reactions "
                         "WHERE chat_id=%(chat_id)s AND message_id=%(message_id)s;",
                         {'chat_id': chat_id, 'message_id': message_id})
        reactions = self.cur.fetchall()

        rated_emoji = None
        chosen_reaction_id = -1
        rated_reaction_id = -1
        res = {}
        for reaction_id, reaction, count in reactions:
            self.cur.execute("SELECT * FROM rates WHERE user_id=%(user_id)s AND reaction_id=%(reaction_id)s;",
                             {'user_id': user_id, 'reaction_id': reaction_id})
            rate = self.cur.fetchone()
            if rate:
                rated_emoji = reaction
                rated_reaction_id = reaction_id
            if reaction == chosen_emoji:
                chosen_reaction_id = reaction_id
            res[reaction] = count

        update_reaction_sql = "UPDATE reactions " \
                              "SET count = %(count)s " \
                              "WHERE id=%(reaction_id)s;"

        if rated_emoji != chosen_emoji:
            res[chosen_emoji] += 1
            # increment count in reactions table for chosen reaction_id
            self.cur.execute(update_reaction_sql, {'reaction_id': chosen_reaction_id,
                                                   'count': res[chosen_emoji]})
            # add user to rate table with chosen_emoji
            self.cur.execute("INSERT INTO rates (user_id, reaction_id) VALUES "
                             "(%(user_id)s, %(reaction_id)s)",
                             {'user_id': user_id, 'reaction_id': chosen_reaction_id})

        if rated_emoji:
            res[rated_emoji] -= 1
            # decrement count in reactions table for rated reaction_id
            self.cur.execute(update_reaction_sql, {'reaction_id': rated_reaction_id,
                                                   'count': res[rated_emoji]})
            # remove user from rate with rated_emoji
            self.cur.execute("DELETE FROM rates "
                             "WHERE reaction_id=%(reaction_id)s",
                             {'reaction_id': rated_reaction_id})
        self.conn.commit()
        return res

    def set_emojis(self, chat_id, emojis: list):
        """
        Set specific emojis for chat and remove old ones.
        """
        self.cur.execute("DELETE FROM chat_reactions WHERE chat_id=%(chat_id)s;",
                         {'chat_id': chat_id})
        for em in emojis:
            self.cur.execute("INSERT INTO chat_reactions (chat_id, reaction) VALUES "
                             "(%(chat_id)s, %(em)s)",
                             {'chat_id': chat_id, 'em': em})
        self.conn.commit()

    def get_emojis(self, chat_id):
        """
        Get emojis from specified chat.
        """
        self.cur.execute("SELECT reaction FROM chat_reactions WHERE chat_id=%(chat_id)s;",
                         {'chat_id': chat_id})
        reactions = self.cur.fetchall()
        return [r[0] for r in reactions]
