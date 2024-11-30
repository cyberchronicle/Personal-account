from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models import user_tag
from schemas import TagsInput, TagsOutput
from dependencies import get_connection


router = APIRouter()


@router.post("/user/{user_id}/tags", response_model=dict)
def save_user_tags(user_id: int, tags_input: TagsInput, conn=Depends(get_connection)):

    """
    Сохраняет теги для пользователя. Игнорирует дубликаты.

    :param user_id: Идентификатор пользователя, для которого добавляются теги.
    :param tags_input: Список тегов, переданных пользователем в формате TagsInput.
    :param conn: Подключение к базе данных, передаётся через Depends.
    :return: Словарь с сообщением о статусе операции.
    :raises HTTPException: Если список тегов пустой или произошла ошибка базы данных.
    """

    if not tags_input.tags:
        raise HTTPException(status_code=400, detail="Tags list cannot be empty")

    for tag in tags_input.tags:
        query = (
            pg_insert(user_tag)
            .values(fk_user=user_id, tag=tag)
            .on_conflict_do_nothing(index_elements=["fk_user", "tag"])
        )
        conn.execute(query)

    return {"message": "Tags successfully saved"}


@router.get("/user/{user_id}/tags", response_model=TagsOutput)
def get_user_tags(user_id: int, conn=Depends(get_connection)):

    """
    Получает список тегов пользователя по ID.

    :param user_id: Идентификатор пользователя, для которого запрашиваются теги.
    :param conn: Подключение к базе данных, передаётся через Depends.
    :return: Объект TagsOutput, содержащий список тегов пользователя.
    :raises HTTPException: Если для указанного пользователя теги не найдены.
    """

    query = select(user_tag.c.tag).where(user_tag.c.fk_user == user_id)
    result = conn.execute(query).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No tags found for this user")

    return {"tags": [row[0] for row in result]}
