import shutil
from pathlib import Path as FSPath
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from util.constant.httpStatusCode import STATUS_CODE, STATUS_MESSAGE

class FilesController:
    """
    파일 업로드 관련 로직 처리
    - 게시글 이미지 업로드
    - 프로필 이미지 업로드
    - 실제 파일을 지정된 디렉터리에 저장 후 경로 반환
    base_dir: 파일을 저장할 디렉터리 경로
    upfile: 업로드된 파일 객체
    반환값: 저장된 파일의 전체 경로
    """
    def _save_file(self, base_dir: str, upfile: UploadFile) -> str:
        if not upfile:
            raise HTTPException(status_code=STATUS_CODE["BAD_REQUEST"], detail=STATUS_MESSAGE["INVALID_FILE"])

        save_dir = FSPath(base_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        file_path = save_dir / upfile.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upfile.file, buffer)

        return str(file_path)

    """
    게시글 이미지 업로드
    - public/image/post 디렉터리에 파일 저장
    - 성공 시 저장 경로 반환
    """
    async def upload_post_file(self, post_file: UploadFile):
        self._save_file("./public/image/post", post_file)
        return {
            "status_code": STATUS_CODE["CREATED"],
            "status_message": STATUS_MESSAGE["FILE_UPLOAD_SUCCESS"],
            "data": {"filePath": f"/public/image/post/{post_file.filename}"},
        }

    """
    프로필 이미지 업로드
    - public/image/profile 디렉터리에 파일 저장
    - 성공 시 파일 경로를 JSON 형식으로 반환
    """
    async def upload_profile_image(self, profile_image: UploadFile):
        self._save_file("./public/image/profile", profile_image)
        return JSONResponse(
            content={"data": {"filePath": f"/public/image/profile/{profile_image.filename}"}}
        )
