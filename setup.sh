python3 -m venv venv
. venv/bin/activate
pip install flask
pip install mysql-connector-python
pip install rsa
pip install cryptography

python3 create_database.py
python3 create_tables.py
