import datetime
import sqlite3
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer


class get_connection:

    def __init__(self):
        pass

    def is_confirmed(self, username):
        connection = self.get_db_connection()
        confirm = connection.execute("SELECT is_confirmed FROM user WHERE username=?",
                           [username]).fetchone()
        return confirm['is_confirmed']

    def get_db_connection(self):
        connection = sqlite3.connect(current_app.config['SQL_DATABASE_URL'])
        connection.row_factory = sqlite3.Row
        return connection

    def ping(self, username):
        connection = self.get_db_connection()
        connection.execute("UPDATE user SET last_seen=? WHERE username=?",
                           (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
        connection.commit()
        connection.close()

    def user_exist(self, username):
        connection = self.get_db_connection()
        current_user = connection.execute("SELECT username FROM user WHERE username=?",
                                          (username,)).fetchone()
        if current_user is not None:
            return True
        else:
            return False

    def add_user(self, username, password):
        """
        return: result--> 1 means insertion was successful
                          if 0 means failed to insert
        """
        connection = self.get_db_connection()

        pass_hash = generate_password_hash(password=password)
        cur = connection.cursor()
        cur.execute('INSERT INTO user(username , password) VALUES (?,?)'
                    , (username, pass_hash))
        connection.commit()
        connection.close()
        return cur.rowcount == 1  # if it's 1 it was successful

    def verify_password(self, input_username, input_password):
        """
        gets the username and password from a user and authenticate him.

        return(job_code,user) --> 0,None: Invalid password
                                  1,user: Valid password
                                 -1,None: username not found
        """
        password = None
        connection = self.get_db_connection()
        user = connection.execute('SELECT * FROM user WHERE username = ?',
                                  (input_username,)).fetchone()
        connection.close()
        if user is None:
            return -1, None  # user not found
        else:
            if check_password_hash(user['password'], input_password):
                return 1, user  # Valid password
            else:
                return 0, None  # Invalid password

    def generate_confirmation_token(self, username):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(username)

    def confirm_token(self, token, expiration=120):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            decoded_data = serializer.loads(token,
                             max_age=expiration
                             )
        except:
            return False

        return decoded_data

