import sqlite3

connection = sqlite3.connect('database/database.db')

with open('user.sql') as f:
    connection.executescript(f.read())

connection.close()
