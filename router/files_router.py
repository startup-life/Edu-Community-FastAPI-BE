from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from controller.files import FilesController

router = APIRouter()

def _ctl() -> FilesController:
    return FilesController()

# 게시물 파일 업로드 엔드포인트
@router.post("/posts/upload/attach-file", status_code=201)
# ...은 파이썬 내장 상수 Ellipsis 객체 - 필수 매개변수임을 나타냄
# upload_post_file이 실행될 때는 postFile이 필수적으로 전달되어야 함
async def upload_post_file(postFile: UploadFile = File(..., alias="postFile")):
    return await _ctl().upload_post_file(postFile)

# 프로필 이미지 업로드 엔드포인트
@router.post("/users/upload/profile-image", status_code=201)
async def upload_profile_image(profileImage: UploadFile = File(..., alias="profileImage")):
    return await _ctl().upload_profile_image(profileImage)