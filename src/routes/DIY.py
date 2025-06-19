import json
from fastapi import APIRouter, Depends, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from helpers import get_settings, Settings
from models import RoomEditor
from controllers import DIYController
from typing import List
from io import BytesIO
from pydantic import BaseModel


#routes ==>> Flow

diy_router = APIRouter(
    prefix="/editor",
    tags=["editor"]
)

@diy_router.post("/{project_id}/upload")
async def upload_data(request: Request, project_id : str, file : UploadFile,
                         app_settings : Settings = Depends(get_settings)):
   
    diy_controller = DIYController()

    is_valid, signal, _ = diy_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "valid_file": is_valid,
                "message": signal
            }
        )

    file_path, file_id = diy_controller.cache_img(file=file, project_id=project_id)
    return JSONResponse(
        content = {
            "valid_file": True,
            "message": signal,
            "project_id": project_id,
            "file_id": str(file_id),
        }
    )
    
    



@diy_router.post("/{project_id}/segment")
async def segment_image(
    request: Request,
    project_id: str,
):
    try:
        data = await request.json()
        
        if "file_id" not in data:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "file_id is required"}
            )
        
        img = DIYController().read_img(project_id, data["file_id"])
        
        editor = RoomEditor()
        preview_path, masks_path, seg_colors = editor.preview_segmentation(img, project_id, data["file_id"])
        
        if preview_path is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Custom mask in use or segmentation failed"}
            )
        
        return {
        "preview_segments_img": FileResponse(preview_path),
        "segments_ids": list(seg_colors.keys()),
        "segments_colors": list(seg_colors.values())
    }
        
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid JSON format"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Processing error: {str(e)}"}
        )

class SegmentRequest(BaseModel):
    file_id: str
    segment_id: str
    color: list[int]
    
@diy_router.post('/{project_id}/change-color')
async def chage_segment_color(
    request: Request,
    data: SegmentRequest,
    project_id: str
):
    data = await request.json()
        
    if "file_id" not in data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "file_id is required"}
        )
        
    if "segment_id" not in data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "segment_id is required"}
        )
        
    if "color" not in data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "color is required"}
        )
    
    diy_controller = DIYController()
    img = diy_controller.read_img(project_id, data["file_id"])
    msk = diy_controller.read_msk(project_id, data['file_id'], data['segment_id'])
    
    
    editor = RoomEditor()


    output_img = editor.change_color(img, msk, data["color"])
    output_img_path, output_img_name = diy_controller.cache_version(output_img,
                                                                    project_id, data["file_id"])
    
    return {
            "Image": FileResponse(output_img_path),
        }


@diy_router.post('/{project_id}/change-texture')
async def change_segment_texture(
    request: Request,
    project_id: str,
    texture_img: UploadFile,
    file_id: str = Form(...),
    segment_id: str = Form(...),
    
):
    
    diy_controller = DIYController()
    img = diy_controller.read_img(project_id, file_id)
    msk = diy_controller.read_msk(project_id, file_id, segment_id)
    
    editor = RoomEditor()
    
    
    output_img =  diy_controller.change_texture(project_id, file_id, editor, img, msk, texture_img)
    
    
    output_img_path, output_img_name = diy_controller.cache_version(output_img,
                                                                    project_id, file_id)

    return {
            "Image": FileResponse(output_img_path),
        }
    
    
@diy_router.post("/{project_id}/save")    
def save_project(project_id: str):
    
    project = DIYController().read_project(project_id)
    return {
        "Project": project
    }

@diy_router.post("/{project_id}/open")    
def open_project():
    return