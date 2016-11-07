import os

API_URL = "http://localhost:9191/"
SECRET_KEY = os.urandom(24)
LOG_FILE = "saltpad.log"
HOST = "0.0.0.0"
EAUTH = "pam"

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sumpad.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
