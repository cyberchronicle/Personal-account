from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, literal
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.connection.session import get_session
from app.database.models.tag import UserTag, Tag
from app.database.models.user import User
from app.tags.schemas import TagsInput, TagsOutput


router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/update", response_model=dict)
def update_user_tags(tags_input: TagsInput,
                     user_id: int = Header(None, alias="x-user-id"),
                     session=Depends(get_session)):

    """
    Сохраняет теги для пользователя. Игнорирует дубликаты.

    :param user_id: Идентификатор пользователя, для которого добавляются теги.
    :param tags_input: Список тегов, переданных пользователем в формате TagsInput.
    :param session: Подключение к базе данных, передаётся через Depends.
    :return: Словарь с сообщением о статусе операции.
    :raises HTTPException: Если список тегов пустой или произошла ошибка базы данных.
    """
    tags_input.tags = list(filter(lambda x: x.strip(), tags_input.tags))
    if not tags_input.tags:
        raise HTTPException(status_code=400, detail="Tags list cannot be empty or some tags is empty")
    
    user_exists_query = select(User).where(User.id == user_id)
    user_exists = session.execute(user_exists_query).fetchone()
    if not user_exists:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    tags_insert_query = (
        pg_insert(Tag)
        .values([{"name": name} for name in tags_input.tags])
        .on_conflict_do_nothing(index_elements=["name"])
    )
    session.execute(tags_insert_query)


    user_tags_query = (
        pg_insert(UserTag)
        .from_select(
            ["user_id", "tag_id", "created_at"],
            select(
                literal(user_id).label("user_id"),
                Tag.id.label("tag_id"),
                literal(datetime.now(timezone.utc)).label("created_at"),
            ).where(Tag.name.in_(tags_input.tags))
        )
        .on_conflict_do_nothing(index_elements=["user_id", "tag_id"])
    )
    session.execute(user_tags_query)
    session.commit()

    return {"message": "Tags successfully saved"}


@router.get("/get", response_model=TagsOutput)
def get_user_tags(user_id: int = Header(None, alias="x-user-id"),
                  session=Depends(get_session)):

    """
    Получает список тегов пользователя по ID.

    :param user_id: Идентификатор пользователя, для которого запрашиваются теги.
    :param session: Подключение к базе данных, передаётся через Depends.
    :return: Объект TagsOutput, содержащий список тегов пользователя.
    :raises HTTPException: Если для указанного пользователя теги не найдены.
    """

    user_exists_query = select(User).where(User.id == user_id)
    user_exists = session.execute(user_exists_query).fetchone()
    if not user_exists:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    query = (
        select(Tag.name)
        .join(UserTag, UserTag.tag_id == Tag.id)
        .where(UserTag.user_id == user_id)
    )
    result = session.execute(query).fetchall()

    if not result:
        raise HTTPException(status_code=404, detail="No tags found for this user")

    return {"tags": [row[0] for row in result]}
