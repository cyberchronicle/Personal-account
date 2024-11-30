from fastapi import APIRouter, UploadFile, Header

from app.s3.minio import upload_file_to_s3, create_key, get_link_on_s3

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/icon-upload")
def icon_upload(file: UploadFile, user_id: int = Header(None, alias="x-user-id")) -> str:
    """Загрузка аватарки пользователя"""
    return upload_file_to_s3(file, create_key("icons", str(user_id)))


@router.get("/icon-get-link")
def icon_get_link(user_id: int = Header(None, alias="x-user-id")) -> str:
    """Получить ссылку на аватарку пользователя"""
    return get_link_on_s3(create_key("icons", str(user_id)))