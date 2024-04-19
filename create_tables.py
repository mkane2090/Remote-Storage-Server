import mysql.connector

def exec_cmd(cursor,cmd):
    try:
        cursor.execute(cmd)
    except Exception as e:
        print('___Error___')
        print(e)
        print('___________')

mydb = mysql.connector.connect(
    host='localhost',
    user='server',
    password='server_password',
    database='storage_server'
)

cursor = mydb.cursor()

exec_cmd(cursor,"CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(255) NOT NULL,password VARCHAR(255) NOT NULL)")

#cursor.execute("SELECT * FROM users")
#result = cursor.fetchall()
#for x in result:
#    print(x[0])
#    print(x[1])
#    print(x[2])

#cursor.execute("SELECT username FROM users")
#result = cursor.fetchall()
#print(result)
