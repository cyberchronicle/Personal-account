from fastapi import APIRouter, UploadFile

from app.s3.minio import upload_file_to_s3

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/user-icon-upload")
def upload_file(file: UploadFile) -> None:
    link = upload_file_to_s3(file)


# @router.get("/user-icon-get-link")
# def upload_file(file: UploadFile) -> None:
#     upload_file_to_s3(file)