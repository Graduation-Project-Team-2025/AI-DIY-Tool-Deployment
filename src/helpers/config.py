from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    HUGGING_FACE_TOKEN: str
    GITHUB_TOKEN: str
    DOCKERHUB_TOKEN: str
    
    FILE_ALLOWED_TYPES: List[str]
    FILE_ALLOWED_SIZE: int
    
    MODELS_WEIGHTS_PATH: str
    UPLOAD_FILES_PATH: str
    
    SEGMENTATION_MODEL_ID: str
    DEPTH_ESTIMATION_MODEL_ID: str
    
    WALL_COLOR: List[int]
    FLOOR_COLOR: List[int]
    CEILING_COLOR: List[int]
    
    model_config = SettingsConfigDict(env_file=".env")

def get_settings():
    return Settings()