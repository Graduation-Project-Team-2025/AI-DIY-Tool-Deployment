import os
from PIL import Image
from .BaseController import BaseController
from fastapi import UploadFile
from models import (ResponseEnum
                    )
from utils import save_file, save_version
import cv2


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
    
    def cache_version(self, file, project_id: str, file_id: str):
        file_path, filename = save_version(file, project_id, file_id,
                                            upload_dir=self.app_settings.UPLOAD_FILES_PATH)
        return file_path, filename 
    
   

    def read_img(self, project_id: str, file_id: str):
        base_dir = os.path.dirname(os.path.dirname(__file__))  # /src/
        upload_path = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH)
        project_path = os.path.join(upload_path, project_id)
        
        matching_files = [
            x for x in os.listdir(project_path)
            if file_id in x and "IMG" in x
        ]
        
        if not matching_files:
            raise FileNotFoundError(f"No image found for file_id: {file_id}")
        
        versioned_files = []
        org_file = None
        
        for filename in matching_files:
            if "VER" in filename:
                versioned_files.append(filename)
            elif "ORG" in filename:
                org_file = filename
        
        if versioned_files:
            def extract_ver_num(f):
                ver_part = f.split("VER")[-1].split(".")[0]  
                return int(ver_part) if ver_part.isdigit() else -1
            
            latest_file = max(versioned_files, key=extract_ver_num)
            img_path = os.path.join(project_path, latest_file)
        elif org_file:
            img_path = os.path.join(project_path, org_file)
        else:
            raise FileNotFoundError(f"No valid image found (missing ORG/VER): {file_id}")
        
        image = Image.open(img_path).convert("RGB")
        return image
    
    def read_msk(self, project_id: str, file_id: str, msk_id: str):
        base_dir = os.path.dirname(os.path.dirname(__file__)) #/src/
        upload_path = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH) #/src/assets/files
        project_path = os.path.join(upload_path, project_id) #/src/assets/files
        
        for x in os.listdir(project_path):
            if file_id in x and "MSK" in x and msk_id in x:
                filename = x
                
        msk_path = os.path.join(project_path, filename)
        msk = cv2.imread(msk_path, cv2.IMREAD_GRAYSCALE)
        
        
        return msk
    
    