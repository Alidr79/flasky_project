from faker import Faker
import random
import sqlite3

def get_connection():
    SQL_URL = "C:/Users/HP 450 G2/PycharmProjects/flasky_project/app/database/database.db"
    connection = sqlite3.connect(SQL_URL)
    connection.row_factory = sqlite3.Row
    return connection

def fake_user(num=100):
    fake = Faker()
    connection = get_connection()
    for i in range(num):
        try:
            connection.execute("INSERT INTO user(username,password,is_confirmed,nick_name,about) "
                               "VALUES(?,?,?,?,?)",
                               (fake.email(), '11111111', 1, fake.user_name(), fake.text()))
            connection.commit()
        except:
            print("error at" , i)

    connection.close()


def fake_post(num=100):
    fake = Faker()
    connection = get_connection()
    response = connection.execute("SELECT id FROM user").fetchall()
    id_list = []
    for i in range(len(response)):
        id_list.append(response[i]['id'])

    for i in range(num):
        try:
            connection.execute("INSERT INTO post(body,author_id) VALUES(?,?)",
                               (fake.text(), random.choice(id_list)))
            connection.commit()
        except:
            print("Post error at",i)

    connection.close()


fake_user(500)
fake_post(500)