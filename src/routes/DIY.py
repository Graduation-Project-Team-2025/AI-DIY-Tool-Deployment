from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse

from helpers import get_settings, Settings
from controllers import DIYController

diy_router = APIRouter(
    prefix="/v1/data",
    tags=["v1", "data"],
)

@diy_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id : str, file : UploadFile,
                         app_settings : Settings = Depends(get_settings)):
   
    diy_controller = DIYController()

    is_valid, signal, _ = diy_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "is_valid": is_valid,
                "message": signal
            }
        )
    return JSONResponse(
        content = {
            "is_valid": True,
            "message": signal,
        }
    )