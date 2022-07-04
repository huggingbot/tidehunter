import os
from os.path import abspath, dirname

from dotenv import load_dotenv

load_dotenv("./.env")

BASE_DIR = dirname(abspath(__file__))

API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

DATABASE_URI = f"sqlite:///{BASE_DIR}/data/data.sqlite3"
