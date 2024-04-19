import mysql.connector

host = 'localhost'

mydb = mysql.connector.connect(
    host = 'localhost',
    username = 'server',
    password = 'server_password')
cursor = mydb.cursor()

cursor.execute('CREATE DATABASE storage_server')
