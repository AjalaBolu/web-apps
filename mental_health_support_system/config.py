"""
config.py — Application Configuration
======================================
Centralised settings for development and production environments.
"""

import os
from datetime import timedelta

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    # -----------------------------------------------------------------
    # SECRET KEY — change this to a long random string in production!
    # -----------------------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mhs-super-secret-key-2024-change-me')

    # -----------------------------------------------------------------
    # DATABASE — update USER / PASSWORD / HOST to match your MySQL setup
    # -----------------------------------------------------------------
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'ilovemum$')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'mental_health_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}/{MYSQL_DB}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -----------------------------------------------------------------
    # SESSION
    # -----------------------------------------------------------------
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # -----------------------------------------------------------------
    # FILE UPLOADS
    # -----------------------------------------------------------------
    UPLOAD_FOLDER       = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH  = 5 * 1024 * 1024          # 5 MB limit
    ALLOWED_EXTENSIONS  = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Active configuration — swap to ProductionConfig before deploying
active_config = DevelopmentConfig
