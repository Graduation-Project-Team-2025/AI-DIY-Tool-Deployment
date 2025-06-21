import os
import re
import cv2
from PIL import Image
import base64
import shutil
from .BaseController import BaseController
from fastapi import UploadFile
from models import (ResponseEnum
                    )
from utils import (
    save_file, 
    save_temp, 
    delete_file,
)


# Controllers ==>> Logic

class DIYController(BaseController):
    def __init__(self):
        super().__init__()
        self.scale_size = 1048576 #from MB to Bytes
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.upload_path = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH)
        

    def validate_uploaded_file(self, file: UploadFile):
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return (
                False,
                ResponseEnum.FILE_TYPE_NOT_SUPPORTED_ENG.value,
                ResponseEnum.FILE_TYPE_NOT_SUPPORTED_AR.value
            )

        if file.size > self.app_settings.FILE_ALLOWED_SIZE * self.scale_size:
            return (
                False,
                ResponseEnum.FILE_SIZE_EXCEEDED_ENG.value,
                ResponseEnum.FILE_SIZE_EXCEEDED_AR.value
            )
        
        return (
            True,
            ResponseEnum.FILE_UPLOADED_SUCCESSFULLY_ENG.value,
            ResponseEnum.FILE_UPLOADED_SUCCESSFULLY_AR.value
        )
        

    def validate_project_id(self, project_id):
        project_path = os.path.join(self.upload_path, project_id)
        
        if os.path.exists(project_path):
            return (
                True,
                ResponseEnum.PROJECT_FOUND_SUCCESSFULLY_ENG.value,
                ResponseEnum.PROJECT_FOUND_SUCCESSFULLY_AR.value
            )
        else:
            return (
                False,
                ResponseEnum.PROJECT_DOES_NOT_EXIST_ENG.value,
                ResponseEnum.PROJECT_DOES_NOT_EXIST_AR.value
            )
        
        
    def validate_file_id(self, file_id, project_id):
        project_path = os.path.join(self.upload_path, project_id)
        filenames = os.listdir(project_path)
        
        pattern_img = r"^(?P<file_id>.+)-IMG-ORG\.(?:png|jpg|jpeg)$"
        file_ids = []
        for fname in filenames:
            match = re.match(pattern_img, fname, re.IGNORECASE)
            if match:
                file_ids.append(match.group("file_id"))
        if file_id in file_ids:
            return (
                True,
                ResponseEnum.FILE_FOUND_SUCCESSFULLY_ENG.value,
                ResponseEnum.FILE_FOUND_SUCCESSFULLY_AR.value
            )
        else:
            return (
                False,
                ResponseEnum.FILE_DOES_NOT_EXIST_ENG.value,
                ResponseEnum.FILE_DOES_NOT_EXIST_AR.value
            )
    
    
    def file_exists(self, project_id, filename):
        project_path = os.path.join(self.upload_path, project_id)
        file_path = os.path.join(project_path, filename)
        if os.path.exists(file_path):
            return (
                True, 
                ResponseEnum.FILE_FOUND_SUCCESSFULLY_ENG.value, 
                ResponseEnum.FILE_FOUND_SUCCESSFULLY_AR.value,
                file_path
            )
        else:
            return (
                False,
                ResponseEnum.FILE_DOES_NOT_EXIST_ENG.value,
                ResponseEnum.FILE_DOES_NOT_EXIST_AR.value,
                ""
            )


    def cache_img(self, file: UploadFile, project_id: str):
        filename , file_id = save_file(file, project_id=project_id,
                                        upload_dir=self.app_settings.UPLOAD_FILES_PATH)
        return filename , file_id 
    
    
    def cache_version(self, file, project_id: str, file_id: str):
        filename , file_id  = save_file(file, project_id, file_id = file_id,
                                            upload_dir=self.app_settings.UPLOAD_FILES_PATH)
        return filename , file_id 
    
    
    def read_project(self, project_id: str):
        project_path = os.path.join(self.upload_path, project_id)
        
        if not os.path.exists(project_path):
            return False, ResponseEnum.FILE_DOES_NOT_EXIST_ENG.value
        filenames = os.listdir(project_path)
        pattern_img = r"^(?P<file_id>.+)-IMG-ORG\.(?:png|jpg|jpeg)$"

        file_ids = []
        for fname in filenames:
            match = re.match(pattern_img, fname, re.IGNORECASE)
            if match:
                file_ids.append(match.group("file_id"))

        project = dict()
        i = 0
        for file_id in file_ids:
            image_content = None
            masks_content = dict()
            depth_content = None

            for filename in filenames:
                full_path = os.path.join(project_path, filename)
                if file_id in filename and "IMG-ORG" in filename:
                    with open(full_path, "rb") as f:
                        image_content = base64.b64encode(f.read()).decode('utf-8')

                if file_id in filename and "MSK" in filename:
                    match = re.match(rf"^{file_id}-MSK:(?P<label>.+)\.png$", filename)
                    if match:
                        label = match.group("label")
                        with open(full_path, "rb") as f:
                            masks_content[label] = base64.b64encode(f.read()).decode('utf-8')

                if file_id in filename and "DPTH" in filename:
                    with open(full_path, "rb") as f:
                        depth_content = base64.b64encode(f.read()).decode('utf-8')

            project[f"file{i}_id"] = file_id
            project[f"files{i}"] = {
                "Image": image_content,
                "Masks": masks_content,
                "Depth": depth_content
            }
            i += 1

        shutil.rmtree(project_path)

        return project
    
    
    def delete_project(self, project_id):
        project_path = os.path.join(self.upload_path, project_id)
        
        shutil.rmtree(project_path)
        return
        

    def read_img(self, project_id: str, file_id: str):
        project_path = os.path.join(self.upload_path, project_id)
        
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
        filename = None
        if versioned_files:
            def extract_ver_num(f):
                ver_part = f.split("VER")[-1].split(".")[0]  
                return int(ver_part) if ver_part.isdigit() else -1
            
            latest_file = max(versioned_files, key=extract_ver_num)
            filename = latest_file
        elif org_file:
            filename = org_file
        else:
            raise FileNotFoundError(f"No valid image found (missing ORG/VER): {file_id}")
        
        img_path = os.path.join(project_path, filename)
        image = Image.open(img_path).convert("RGB")
        return image, filename
    
    
    def read_msk(self, project_id: str, file_id: str, msk_id: str):
        project_path = os.path.join(self.upload_path, project_id) 
        
        for x in os.listdir(project_path):
            if file_id in x and "MSK" in x and msk_id in x:
                filename = x
                
        msk_path = os.path.join(project_path, filename)
        msk = cv2.imread(msk_path, cv2.IMREAD_GRAYSCALE)
        
        return msk
    
    
    def change_texture(self, project_id, file_id, editor, img, msk, texture_img):
        texture_path, _ = save_temp(texture_img, project_id, self.app_settings.UPLOAD_FILES_PATH)
        texture = cv2.imread(texture_path)
        texture = cv2.cvtColor(texture, cv2.COLOR_BGR2RGB)
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        save_dir = os.path.join(base_dir, self.app_settings.UPLOAD_FILES_PATH)
        project_dir = os.path.join(save_dir, project_id)
        
        depth_filename = f"{file_id}-DPTH.png"
        depth_path = os.path.join(project_dir, depth_filename)
        
        depth = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
        
        output_img = editor.warp_texture_with_depth(img, texture, depth, msk)
        delete_file(texture_path)
        
        return output_img
        
        
        
    def open_project(self, project_id: str, project_data: dict):
        project_path = os.path.join(self.upload_path, project_id)
        os.makedirs(project_path, exist_ok=True)

        for key, files in project_data.items():
            if key.startswith("files"):
                index = key.replace("files", "")   # get the number part
                file_id_key = f"file{index}_id"

                # get the file_id value from the corresponding key
                file_id = project_data.get(file_id_key, key)

                # Save main image
                image_b64 = files.get("Image")
                if image_b64:
                    image_path = os.path.join(project_path, f"{file_id}-IMG-ORG.png")
                    with open(image_path, "wb") as f:
                        f.write(base64.b64decode(image_b64))

                # Save masks
                masks = files.get("Masks", {})
                for label, mask_b64 in masks.items():
                    mask_path = os.path.join(project_path, f"{file_id}-MSK:{label}.png")
                    with open(mask_path, "wb") as f:
                        f.write(base64.b64decode(mask_b64))

                # Save depth image
                depth_b64 = files.get("Depth")
                if depth_b64:
                    depth_path = os.path.join(project_path, f"{file_id}-DPTH.png")
                    with open(depth_path, "wb") as f:
                        f.write(base64.b64decode(depth_b64))

        return True

        
        