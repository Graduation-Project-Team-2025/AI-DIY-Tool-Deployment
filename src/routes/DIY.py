import json
from fastapi import APIRouter, Depends, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse
from helpers import get_settings, Settings
from models import RoomEditor
from controllers import DIYController
from pydantic import BaseModel
from typing import List


diy_router = APIRouter(
    prefix="/editor",
    tags=["editor"]
)

@diy_router.post("/{project_id}/upload")
async def upload_data(project_id : str, file : UploadFile):
   
    diy_controller = DIYController()
    is_valid, signal_eng, signal_ar = diy_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "valid_file": is_valid,
                "message": signal_eng
            }
        )

    _, file_id = diy_controller.cache_img(file=file, project_id=project_id)
    return JSONResponse(
        content = {
            "valid_file": True,
            "message": signal_eng,
            "project_id": project_id,
            "file_id": str(file_id),
        }
    )



@diy_router.post("/{project_id}/segment")
async def segment_image( request: Request, project_id: str):
    
    data = await request.json()
    
    diy_controller = DIYController()
    if "file_id" not in data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Error": "File ID is required"}
        )
    valid, signal_eng, signal_ar = diy_controller.validate_project_id(project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
    valid, signal_eng, signal_ar = diy_controller.validate_file_id(data["file_id"], project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
        
    editor = RoomEditor()
    img, img_filename = diy_controller.read_img(project_id, data["file_id"])
    preview_img_filename, seg_colors = editor.preview_segmentation(img, project_id, data["file_id"])
    
    if preview_img_filename is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": "Segmentation failed"
                }
        )
        
    base_url = str(request.base_url)
    preview_url = base_url + f"image/{project_id}/{preview_img_filename}"
    image_url = base_url + f"image/{project_id}/{img_filename}"
    return {
        "preview_segments_img_url": preview_url,
        "image_url": image_url,
        "segments_ids": list(seg_colors.keys()),
        "segments_colors": list(seg_colors.values())
        }
        
   

class SegmentColorPair(BaseModel):
    segment_id: str
    color: List[int]

class SegmentRequest(BaseModel):
    file_id: str
    segments: List[SegmentColorPair]

@diy_router.post('/{project_id}/change-color')
async def change_segment_colors(
    request: Request,
    data: SegmentRequest,
    project_id: str
):
    diy_controller = DIYController()

    valid, signal_eng, _ = diy_controller.validate_project_id(project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Error": signal_eng}
        )

    valid, signal_eng, _ = diy_controller.validate_file_id(data.file_id, project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Error": signal_eng}
        )

    if not data.segments:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Error": "At least one segment-color pair is required"}
        )

    img, _ = diy_controller.read_img(project_id, data.file_id)
    editor = RoomEditor()

    for item in data.segments:
        msk = diy_controller.read_msk(project_id, data.file_id, item.segment_id)
        img = editor.change_color(img, msk, item.color)  

    output_img_name, _ = diy_controller.cache_version(img, project_id, data.file_id)
    base_url = str(request.base_url)
    url = base_url + f"image/{project_id}/{output_img_name}"

    return {"Image": url}



@diy_router.post('/{project_id}/change-texture')
async def change_segment_texture(
    request: Request,
    project_id: str,
    texture_img: UploadFile,
    file_id: str = Form(...),
    segment_id: str = Form(...),
):
    diy_controller = DIYController()
    valid, signal_eng, signal_ar = diy_controller.validate_project_id(project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
    valid, signal_eng, signal_ar = diy_controller.validate_file_id(file_id, project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
    img, _ = diy_controller.read_img(project_id, file_id)
    msk = diy_controller.read_msk(project_id, file_id, segment_id)
    
    editor = RoomEditor()
    output_img =  diy_controller.change_texture(project_id, file_id, editor, img, msk, texture_img)
    output_img_name, _ = diy_controller.cache_version(output_img, project_id, file_id)
    
    base_url = str(request.base_url)
    url = base_url + f"image/{project_id}/{output_img_name}"

    return {"Image": url}
    
    
@diy_router.post("/{project_id}/save")    
def save_project(project_id: str):
    diy_controller = DIYController()
    valid, signal_eng, signal_ar = diy_controller.validate_project_id(project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
        
    project = diy_controller.read_project(project_id)
    return {
        "Project_ID" : project_id,
        "Project": project
    }

@diy_router.post("/{project_id}/exit")    
def exit_project(project_id:str):
    diy_controller = DIYController()
    valid, signal_eng, signal_ar = diy_controller.validate_project_id(project_id)
    if not valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "Error": signal_eng
            }
        )
        
    diy_controller.delete_project(project_id)
    return {"message": "Success!"}


@diy_router.post("/{project_id}/open")
async def load_project(project_id: str, request: Request):
    diy_controller = DIYController()

    payload = await request.json()
    project_data = payload.get("Project")

    if not project_data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"Error": "No project data provided."}
        )

    diy_controller.open_project(project_id, project_data)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Project {project_id} files restored successfully."}
    )