import os

from app import app
from config import HOST, PORT


if __name__ == '__main__':
    app.run(host=HOST, debug=True, port=int(PORT))