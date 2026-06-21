from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "LRMIS"
    environment: str = "development"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "lrmis"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "LRMIS"),
        environment=os.getenv("ENVIRONMENT", "development"),
        mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db_name=os.getenv("MONGODB_DB_NAME", "lrmis"),
    )
