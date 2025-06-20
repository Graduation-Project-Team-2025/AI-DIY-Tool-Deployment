from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, FileResponse
from controllers import DIYController


image_router = APIRouter(
    prefix="/image",
    tags=["image"],
)

@image_router.get("/{project_id}/{image_filename}")
async def show_image(project_id: str, image_filename:str):
    diy_controller = DIYController()
    is_valid, message, _ = diy_controller.validate_project_id(project_id)
    if is_valid:
        valid, message, _, image_path = diy_controller.file_exists(project_id, image_filename)
        if not valid:
            return JSONResponse(
                status_code = status.HTTP_400_BAD_REQUEST,
                content = {
                    "Error": message
                }
            )
        else:
            print(image_path)
            return FileResponse(image_path)
    else:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "Error": message
            }
        )
