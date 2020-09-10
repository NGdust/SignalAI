import os

HOST = '0.0.0.0'
PORT = 5004
if 'DEBUG' in os.environ:
    HOST = os.environ.get('WEB_IP')
    PORT = os.environ.get('WEB_PORT')


class Configuration:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:nigative32@localhost:5432/test'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.getcwd() + '/transite/'

    if 'DEBUG' in os.environ:
        DEBUG = False
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')