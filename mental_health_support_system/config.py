import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'mhs-super-secret-key-2024-change-me'
    )

    MYSQL_HOST = os.environ.get('MYSQLHOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQLPORT', '3306')
    MYSQL_USER = os.environ.get('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQLPASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQLDATABASE', 'mental_health_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


active_config = ProductionConfig