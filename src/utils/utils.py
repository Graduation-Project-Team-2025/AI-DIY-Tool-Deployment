import os
import re
import cv2
from PIL import Image
from uuid import uuid4
from typing import List
from fastapi import UploadFile
from helpers import get_settings
from huggingface_hub import login, snapshot_download 


def get_file_ext(filename : str):
    return filename.split('.')[-1]

def save_file(file: UploadFile, project_id: str, upload_dir: str):

    base_dir_path = os.path.dirname(os.path.dirname(__file__)) # /src/..
    full_upload_dir = os.path.join(base_dir_path, upload_dir) #/src/assets/files

    project_path = os.path.join(full_upload_dir, project_id)
    os.makedirs(project_path, exist_ok=True)

    ext = get_file_ext(file.filename)

    file_id = uuid4()
    filename = f"{file_id}-IMG-ORG.{ext}"
    file_path = os.path.join(project_path, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path, file_id

def save_temp(file: UploadFile, project_id: str, upload_dir: str):

    base_dir_path = os.path.dirname(os.path.dirname(__file__)) # /src/..
    full_upload_dir = os.path.join(base_dir_path, upload_dir) #/src/assets/files

    project_path = os.path.join(full_upload_dir, project_id)
    os.makedirs(project_path, exist_ok=True)

    ext = get_file_ext(file.filename)

    file_id = uuid4()
    filename = f"{file_id}-TEMP.{ext}"
    file_path = os.path.join(project_path, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path, file_id

def delete_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found, skipping delete: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")



def download_models(model_ids: List[str], save_path: str):
    os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "3600"
    app_settings = get_settings()
    HUGGING_FACE_TOKEN = app_settings.HUGGING_FACE_TOKEN
    login(token=HUGGING_FACE_TOKEN)
    
    models_path = []
    for model_id in model_ids:
        model_name = model_id.split('/')[-1]
        model_save_path = os.path.join(save_path, model_name)
        models_path.append(model_save_path)
        if not os.path.isdir(model_save_path):
            print(f"Downloading {model_name}...", end=" ")

            snapshot_download(repo_id=model_id,
                              use_auth_token=True,
                              local_dir=model_save_path,
                              resume_download=True)
            print("Done.")
        else:
            print(f"{model_name} already exists")

    return models_path


def save_version(file, project_id: str, file_id: str, upload_dir:str):
    base_dir = os.path.dirname(os.path.dirname(__file__)) #/src/
    upload_path = os.path.join(base_dir, upload_dir)
    project_path = os.path.join(upload_path, project_id)
    
    version=-1
    for file_itr in os.listdir(project_path):
        if file_id in file_itr and "IMG" in file_itr:
            ext = get_file_ext(file_itr)
            if "VER" in file_itr:
                match = re.search(r"VER(\d+)\.", file_itr)
                older = match.group(1)
                if int(older) > version:
                    version = int(older) 
                    
    version += 1

                
    filename = f"{file_id}-IMG-VER{version}.{ext}"
    file_path = os.path.join(project_path, filename)
    
    bgr_image = cv2.cvtColor(file, cv2.COLOR_RGB2BGR) 
    cv2.imwrite(file_path, bgr_image)
        
    return file_path, filename
    
