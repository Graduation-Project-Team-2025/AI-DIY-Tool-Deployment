from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    HUGGING_FACE_TOKEN: str
    GITHUB_TOKEN: str
    FILE_ALLOWED_TYPES: List[str]
    FILE_ALLOWED_SIZE: int
    MODELS_WEIGHTS_PATH: str
    
    model_config = SettingsConfigDict(env_file=".env")

def get_settings():
    return Settings()