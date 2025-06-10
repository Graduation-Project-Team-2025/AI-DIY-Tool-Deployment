import json
from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from helpers import get_settings, Settings
from models import RoomEditor
from controllers import DIYController

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
    # try:
    # 1. Parse JSON data
    data = await request.json()
    
    # 2. Validate required fields
    if "file_id" not in data:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "file_id is required"}
        )
    
    # 3. Get image using your controller
    img = DIYController().read_img(project_id, data["file_id"])
    
    # 4. Process image
    editor = RoomEditor()
    preview_path, masks_path = editor.preview_segmentation(img, project_id, data["file_id"])
    
    if preview_path is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Custom mask in use or segmentation failed"}
        )
    
    # 5. Return preview image
    return FileResponse(preview_path)
        
    # except json.JSONDecodeError:
    #     return JSONResponse(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         content={"error": "Invalid JSON format"}
    #     )
    # except Exception as e:
    #     return JSONResponse(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         content={"error": f"Processing error: {str(e)}"}
    #     )

# @diy_router.post('/{project_id}/edit')
# async def edit_image():
#     image_file = request.files.get('image')
#     texture_file = request.files.get('floor_texture')
#     color_wall = request.form.get('color_wall')  # e.g., "255,0,0"
#     color_ceiling = request.form.get('color_ceiling')  # e.g., "0,255,0"

#     if not image_file:
#         return jsonify({"error": "Image file is required"}), 400

#     image = Image.open(image_file).convert("RGB")
#     wall_rgb = tuple(map(int, color_wall.split(","))) if color_wall else None
#     ceiling_rgb = tuple(map(int, color_ceiling.split(","))) if color_ceiling else None

#     texture_path = None
#     if texture_file:
#         tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
#         texture_file.save(tmp.name)
#         texture_path = tmp.name

#     output_img, _ = editor.process(image, color_wall=wall_rgb, color_ceiling=ceiling_rgb, floor_texture=texture_path)
#     output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
#     output_img.save(output_path)

#     return send_file(output_path, mimetype='image/png')