from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import sel
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models import UserTag, Tag
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

    tags_insert_query = (
        pg_insert(Tag)
        .values([{"name": name} for name in tags_input.tags])
        .on_conflict_do_nothing(index_elements=["name"])
    )
    conn.execute(tags_insert_query)


    user_tags_query = (
        pg_insert(UserTag)
        .from_select(
            ["user_id", "tag_id", "created_at"],
            select(
                user_id.label("user_id"),
                Tag.id.label("tag_id"),
                datetime.now(timezone.utc).label("created_at"),
            ).where(Tag.name.in_(tags_input.tags))
        )
        .on_conflict_do_nothing(index_elements=["user_id", "tag_id"])
    )
    conn.execute(user_tags_query)

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

    query = (
        select(Tag.name)
        .join(UserTag, UserTag.tag_id == Tag.id)
        .where(UserTag.user_id == user_id)
    )
    result = conn.execute(query).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No tags found for this user")

    return {"tags": [row[0] for row in result]}
