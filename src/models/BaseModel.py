from helpers import get_settings

class BaseModel:
    def __init__(self):
        self.app_settings = get_settings()