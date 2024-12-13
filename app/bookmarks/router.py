from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection.session import get_session
from app.database.models.user import User
from app.database.models.bookmark import Bookmark, Shelf, BookmarkInShelf
from app.bookmarks.schema import (ReturnShelves, CreateShelf,
                                  ReturnBookmarks, AddBookmark, RemoveBookmark, RemoveShelf)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, delete


router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


# проверяет существование пользователя
def check_user(user_id: int, session):
    user_exists_query = select(User).where(User.id.is_(user_id))
    user_exists = session.execute(user_exists_query).fetchone()
    if not user_exists:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")


@router.get("/get_shelves", response_model=List[ReturnShelves])
def get_shelves(user_id: int = Header(None, alias="x-user-id"),
                session=Depends(get_session)):

    check_user(user_id, session)

    # формируем и отправляем запрос
    get_shelves_query = (select(Shelf.id, Shelf.name, Bookmark.title)
                         .join(BookmarkInShelf, Shelf.id == BookmarkInShelf.fk_shelf)
                         .join(Bookmark, Bookmark.id == BookmarkInShelf.fk_bookmark)
                         .where(Shelf.fk_user.is_(user_id))
                         .group_by(Shelf.id, Shelf.name))
    result = session.execute(get_shelves_query).fetchall()
    if not result:
        raise HTTPException(status_code=404, detail="No bookmarks found for this user")

    # форматируем ответ
    response_list: List[ReturnShelves] = []
    last_id = -1
    counter = 0
    new_shelf = ReturnShelves(id=-1, name="None", bookmarks=[])
    for shelf in result:
        if shelf.id != last_id:
            counter = 0
            if last_id != -1:
                response_list.append(new_shelf)
            last_id = shelf.id
            new_shelf = ReturnShelves(id=shelf[0], name=shelf[1], bookmarks=[])
        if counter > 2:
            continue
        counter += 1
        new_shelf.bookmarks.append(shelf[2])
    response_list.append(new_shelf)
    return response_list


@router.get("/get_bookmarks", response_model=List[ReturnBookmarks])
def get_bookmarks(shelf_id: int,
                  user_id: int = Header(None, alias="x-user-id"),
                  session=Depends(get_session)):

    check_user(user_id, session)

    # формируем и отправляем запрос
    get_bookmarks_query = (select(Bookmark.id, Bookmark.title)
                           .join(BookmarkInShelf, shelf_id == BookmarkInShelf.fk_shelf)
                           .join(Bookmark, Bookmark.id == BookmarkInShelf.fk_bookmark))
    result = session.execute(get_bookmarks_query).fetchall()

    return result


@router.post("/create_shelf", response_model=dict)
def create_shelf(shelf_name: CreateShelf,
                 user_id: int = Header(None, alias="x-user-id"),
                 session=Depends(get_session)):

    check_user(user_id, session)

    # формируем запрос
    create_shelf_query = (
        pg_insert(Shelf)
        .values(name=shelf_name, fk_user=user_id)
    )

    # пытаемся провести транзакцию
    try:
        session.execute(create_shelf_query)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Shelf successfully created"}


@router.post("/add_bookmark", response_model=dict)
def add_bookmark(new_bookmark: AddBookmark,
                 user_id: int = Header(None, alias="x-user-id"),
                 session=Depends(get_session)):

    check_user(user_id, session)

    # проверяем наличие полки
    check_shelf = (
        select(Shelf).where(Shelf.id.is_(new_bookmark.shelf_id))
    )
    if not check_shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    # формируем запросы
    add_bookmark_query = (
        pg_insert(Bookmark)
        .values(bookmark_id=new_bookmark.bookmark_id, title=new_bookmark.title)
    )

    add_link_query = (
        pg_insert(BookmarkInShelf)
        .values(fk_bookmark=new_bookmark.bookmark_id, fk_shelf=new_bookmark.shelf_id)
    )

    # пытаемся провести транзакцию
    try:
        session.execute(add_bookmark_query)
        session.execute(add_link_query)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Bookmark successfully added"}


@router.post("/delete_bookmark_from_shelf", response_model=dict)
def delete_bookmark_from_shelf(bookmark_to_remove: RemoveBookmark,
                               user_id: int = Header(None, alias="x-user-id"),
                               session=Depends(get_session)):

    check_user(user_id, session)

    # проверяем наличие полки
    check_shelf = (
        select(Shelf).where(Shelf.id.is_(bookmark_to_remove.shelf_id))
    )
    if not check_shelf:
        raise HTTPException(status_code=404, detail="Shelf not found")

    # формируем запрос
    remove_bookmark_query = (
        delete(BookmarkInShelf)
        .where(BookmarkInShelf.fk_bookmark.is_(bookmark_to_remove.bookmark_id))
        .where(BookmarkInShelf.fk_shelf.is_(bookmark_to_remove.shelf_id))
    )

    # пытаемся провести транзакцию
    try:
        session.execute(remove_bookmark_query)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Bookmark removed from shelf"}


@router.post("/delete_shelf", response_model=dict)
def delete_shelf(shelf_to_remove: RemoveShelf,
                 user_id: int = Header(None, alias="x-user-id"),
                 session=Depends(get_session)):
    check_user(user_id, session)

    # проверяем наличие полки
    check_shelf = (
        select(Shelf).where(Shelf.id.is_(shelf_to_remove.shelf_id))
    )
    if not check_shelf:
        return {"message": "Nothing to remove"}

    # формируем запросы
    remove_shelf_query = (
        delete(Shelf)
        .where(Shelf.id.is_(shelf_to_remove.shelf_id))
    )
    remove_link_query = (
        delete(BookmarkInShelf)
        .where(BookmarkInShelf.fk_shelf.is_(shelf_to_remove.shelf_id))
    )

    # пытаемся провести транзакцию
    try:
        session.execute(remove_shelf_query)
        session.execute(remove_link_query)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"message": "Shelf removed"}
