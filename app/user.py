from flask_login import UserMixin
from . import login_manager
from .database import get_connection


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
        self.authenticated = False

    def get_username(self):
        return self.username

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return self.authenticated

    def get_id(self):
        return self.id


@login_manager.user_loader
def load_user(user_id):
    connection = get_connection().get_db_connection()
    cursor = connection.cursor()
    user = cursor.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        return None
    else:
        return User(int(user['id']), user['username'], user['password'])
