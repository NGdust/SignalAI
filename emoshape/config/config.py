import os

EMOSHAPE_HOST = '127.0.0.1'
EMOSHAPE_SECRET = 'xGyrpOpB/X+zpKtTgspeluOfE3TOmWV6'

RABBITMQ_HOST = '0.0.0.0'
RABBITMQ_LOGIN = 'rabbitmq'
RABBITMQ_PASSWORD = 'rabbitmq'

if 'DEBUG' in os.environ:
    EMOSHAPE_HOST = os.environ.get('EMOSHAPE_HOST')
    EMOSHAPE_SECRET = os.environ.get('EMOSHAPE_SECRET')

    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
    RABBITMQ_LOGIN = os.environ.get('RABBITMQ_DEFAULT_USER')
    RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_DEFAULT_PASS')

