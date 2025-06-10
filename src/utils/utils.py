from fastapi import UploadFile
import os
from uuid import uuid4
from helpers import get_settings
from huggingface_hub import login, snapshot_download 
from typing import List

def get_file_ext(filename : str):
    return filename.split('.')[-1]

def save_file(file: UploadFile, upload_dir: str):

    base_dir_path = os.path.dirname(os.path.dirname(__file__)) # /src/..
    full_upload_dir = os.path.join(base_dir_path, upload_dir)

    os.makedirs(full_upload_dir, exist_ok=True)
    
    ext = get_file_ext(file.filename)

    file_ids = []
    if os.path.exists(upload_dir) :
        file_ids = [x.split(".")[0] for x in os.listdir(upload_dir)]         
    
    while True:
        file_id = str(uuid4())
        if file_id not in file_ids:
            break

    filename = f"{uuid4()}.{ext}"
    file_path = os.path.join(full_upload_dir, filename)
    print(f"DEBUG: Trying to save to: {file_path}")
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return file_path, filename

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

