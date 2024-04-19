from flask import Flask
from flask import request, send_file
from hashlib import sha512, md5
from datetime import datetime
from cryptography.fernet import Fernet
import mysql.connector
import os, rsa, ast

print(datetime.today())

mydb = mysql.connector.connect(
    host='localhost',
    user='server',
    password='server_password',
    database='storage_server'
)

cursor = mydb.cursor()

app = Flask(__name__)

directory = os.getcwd()
publickey, privatekey = rsa.newkeys(2048)
client_keys = {}

def tally_users():
    global cursor
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    return len(result)

def decode(val):
    '''
        In order to get back to the unencrypted input, I must
        convert the string back into a list of integers,
        then convert the list back into bytes, then decrypt the
        bytes using the private key, then decode the decrypted
        value from utf-8 into a string.
    '''
    global privatekey
    array = ast.literal_eval(val)   # Convert string to list
    encrypted = bytes(array)    # Convert list of ints to bytes
    return rsa.decrypt(encrypted,privatekey).decode('utf-8')

def encode(val,key):
    return str(list(rsa.encrypt(val.encode('utf-8'),key)))

@app.route('/retrieve-public-key',methods=['POST'])
def retrieve_public_key():
    global publickey
    state = publickey.__getstate__()
    return {'n':state[0],'e':state[1]}

@app.route('/new-user',methods = ['POST'])
def add_new_user():
    global mydb, cursor, directory
    username = decode(request.form['username'])
    password = decode(request.form['password'])
    key_vals = request.form['publickey']
    client_key = rsa.PublicKey(key_vals[0],key_vals[1])
    # Single quotes are required around VARCHAR data entries
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    result = cursor.fetchall()
    if len(result) > 0:
        return {'response':encode('False',client_key),'message':encode('User Already Exists',client_key)}
    hash = sha512(password.encode('utf-8')).hexdigest()
    id = tally_users() + 1
    cursor.execute(f"INSERT INTO users (id,username,password) VALUES ({id},'{username}','{hash}')")
    mydb.commit()
    print(cursor.rowcount, "record inserted.")
    client_keys[username] = client_key
    return {'response':encode('True',client_key)}

@app.route('/login',methods = ['POST'])
def login():
    global client_keys
    username = decode(request.form['username'])
    password = decode(request.form['password'])
    key_vals = request.form['publickey']
    key_vals = ast.literal_eval(key_vals)
    print(type(key_vals))
    print(type(key_vals[0]),type(key_vals[1]))
    client_key = rsa.PublicKey(int(key_vals[0]),int(key_vals[1]))
    hash = sha512(password.encode('utf-8')).hexdigest()
    cursor.execute(f"SELECT * FROM users WHERE username='{username}'")
    result = cursor.fetchall()
    if len(result) == 0:
        return {'response': encode('False',client_key),
                'message':encode('User not found',client_key)}
    elif len(result) > 1:
        return {'response': encode('False',client_key),
                'message':encode('Repeat users found',client_key)}
    if username == result[0][1] and hash == result[0][2]:
        print('Valid Login')
        client_keys[username] = client_key
        return {'response':encode('True',client_key)}
    return {'response':encode('False',client_key)}

@app.route('/logout',methods = ['POST'])
def logout():
    global client_keys
    username = decode(request.form['username'])
    if username in client_keys.keys():
        key = client_keys[username]
        del client_keys[username]
        return {'response':'True'}
    return {'response':'True'}

@app.route('/store-file',methods = ['POST'])
def store_file():
    '''
    This function will either update an existing file or store a new file
    '''
    global directory
    username = decode(request.form['username'])
    sym_key = bytes(ast.literal_eval(decode(request.form['sym_key'])))
    fernet = Fernet(sym_key)
    key = client_keys[username]
    try:
        os.mkdir(directory + '/folders' + f'/{username}_files')
    except FileExistsError:
        print('Folder already exists')
    fname = decode(request.form['file_name'])
    #if os.path.isfile(directory + f'/folders/{username}_files/{fname}'):
    #    return {'response':'File already exists'}
    request.files['file'].save(directory + '/temp.txt')

    f = open(directory + '/temp.txt','rb')
    data = f.read()
    f.close()

    data = fernet.decrypt(data)
    f = open(directory + f'/folders/{username}_files/{fname}','wb')
    f.write(data)
    f.close()

    val = md5(open(directory + f'/folders/{username}_files/{fname}','rb').read()).hexdigest()
    return {'response':encode('File saved',key),'hash':encode(val,key)}

@app.route('/retrieve-file',methods = ['POST'])
def retrieve_file():
    global directory
    username = decode(request.form['username'])
    fname = decode(request.form['file_name'])
    key = client_keys[username]
    sym_key = Fernet.generate_key()
    fernet = Fernet(sym_key)
    if not os.path.isfile(directory + f'/folders/{username}_files/{fname}'):
        return {'response':encode('File does not exist',key)}
    val = md5(open(directory + f'/folders/{username}_files/{fname}','rb').read()).hexdigest()
    return {'key':encode(str(list(sym_key)),key),'hash':encode(val,key),'file':str(list(fernet.encrypt(open(directory + f'/folders/{username}_files/{fname}','rb').read())))}

@app.route('/remove-file',methods = ['POST'])
def remove_file():
    global directory
    username = decode(request.form['username'])
    fname = decode(request.form['file_name'])
    key = client_keys[username]
    if not os.path.isfile(directory + f'/folders/{username}_files/{fname}'):
        return {'response':encode('File does not exist',key)}
    os.remove(directory + f'/folders/{username}_files/{fname}')
    return {'response':encode('File deleted',key)}

@app.route('/list-stored-files',methods = ['POST'])
def list_stored_files():
    global directory, client_keys
    username = decode(request.form['username'])
    key = client_keys[username]
    try:
        files = os.listdir(directory + f'/folders/{username}_files')
        return {'response':encode(str(files),key)}
    except FileNotFoundError as e:
        print('User directory not found')
        return {'response':encode('Invalid User',key)}

if __name__ == '__main__':
    app.run(host = '0.0.0.0')
