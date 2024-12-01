from fastapi import APIRouter, UploadFile, Header, Depends, HTTPException

from app.s3.minio import get_s3, S3Service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/icon-upload")
def icon_upload(file: UploadFile,
                user_id: int = Header(None, alias="x-user-id"),
                s3: S3Service = Depends(get_s3)) -> str:
    """Загрузка аватарки пользователя"""
    return s3.upload_file(file, s3.create_key("icons", str(user_id)))


@router.get("/icon-get-link")
def icon_get_link(user_id: int = Header(None, alias="x-user-id"),
                  s3: S3Service = Depends(get_s3)) -> str:
    """Получить ссылку на аватарку пользователя"""
    try:
        return s3.get_link(s3.create_key("icons", str(user_id)))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")