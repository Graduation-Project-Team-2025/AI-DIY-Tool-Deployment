import os
from PIL import Image
from .BaseController import BaseController
from fastapi import UploadFile
from models import (ResponseEnum
                    )
from utils import save_file

# Controllers ==>> Logic

class DIYController(BaseController):
    def __init__(self):
        super().__init__()
        self.scale_size = 1048576 #from MB to Bytes

    def validate_uploaded_file(self, file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseEnum.FILE_TYPE_NOT_SUPPORTED_ENG.value, ResponseEnum.FILE_TYPE_NOT_SUPPORTED_AR.value

        if file.size > self.app_settings.FILE_ALLOWED_SIZE * self.scale_size:
            return False, ResponseEnum.FILE_SIZE_EXCEEDED_ENG.value, ResponseEnum.FILE_SIZE_EXCEEDED_AR.value
        
        return True, ResponseEnum.FILE_UPLOADED_SUCCESSFULLY_ENG.value,  ResponseEnum.FILE_UPLOADED_SUCCESSFULLY_AR.value

    def cache_img(self, file: UploadFile, project_id: str):
        file_path, filename = save_file(file, project_id=project_id,
                                        upload_dir=self.app_settings.UPLOAD_FILES_PATH)
        return file_path, filename 
    
    def read_img(self, project_id: str, file_id: str):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        project_path = os.path.join(self.app_settings.UPLOAD_FILES_PATH, project_id)
        for x in os.listdir(project_path):
            if file_id in x and "mask" not in x and "seg" not in x:
                filename = x
                
        img_path = os.path.join(project_path, filename)

        image = Image.open(img_path).convert("RGB")
        return image
    