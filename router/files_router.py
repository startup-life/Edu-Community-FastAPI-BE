from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from controller.files import FilesController

router = APIRouter()

def _ctl() -> FilesController:
    return FilesController()

@router.post("/posts/upload/attach-file", status_code=201)
async def upload_post_file(postFile: UploadFile = File(..., alias="postFile")):
    return await _ctl().upload_post_file(postFile)

@router.post("/users/upload/profile-image", status_code=201)
async def upload_profile_image(profileImage: UploadFile = File(..., alias="profileImage")):
    return await _ctl().upload_profile_image(profileImage)
