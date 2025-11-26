import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "")
    DB_NAME = os.getenv("DB_NAME", "qircuitlearn")
    JSONIFY_PRETTYPRINT_REGULAR = False
