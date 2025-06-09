from fastapi import UploadFile
import os
from uuid import uuid4

def get_file_ext(filename : str):
    return filename.split('.')[-1]

def save_file(video: UploadFile, upload_dir : str="assets/files"):
    os.makedirs(upload_dir, exist_ok=True)
    base_dir_path = os.path.dirname(os.path.dirname(__file__)) #/src/
    
    dir_path = os.path.join(base_dir_path, upload_dir)
    ext = get_file_ext(video.filename)
    filename = f"{uuid4()}.{ext}"
    file_path = os.path.join(dir_path, filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(video.file.read())

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

