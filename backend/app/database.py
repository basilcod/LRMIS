from pymongo import MongoClient

from app.config import get_settings


def get_database():
    settings = get_settings()
    client = MongoClient(settings.mongodb_uri)
    return client[settings.mongodb_db_name]
