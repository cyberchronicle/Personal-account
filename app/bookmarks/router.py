from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection.session import get_session
from app.database.models.user import User
from app.database.models.bookmark import Bookmark, Shelf, BookmarkInShelf
from app.bookmarks.schema import (ReturnShelves, CreateShelf, ReturnOnlyShelves,
                                  ReturnBookmarks, AddBookmark, RemoveBookmark,
                                  RemoveShelf)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, delete
from sqlalchemy.schema import MetaData

from app.database.connection.session import engine


router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


# проверяет существование пользователя
def check_user(user_id: int, session) -> None:
    user_exists_query = select(User).where(User.id == user_id)
    user_exists = session.execute(user_exists_query).fetchone()
    if not user_exists:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")


@router.get("/get_only_shelves", response_model=ReturnOnlyShelves)
def get_only_shelves(user_id: int = Header(None, alias="x-user-id"),
                     session=Depends(get_session)):
    check_user(user_id, session)

    get_only_shelves_query = (select(Shelf.id)
                              .where(Shelf.fk_user == user_id))
    result = session.execute(get_only_shelves_query).fetchall()
    if not result:
        return {"id": []}
    only_shelves = []
    for element in result:
        only_shelves.append(element[0])
    return {"id": only_shelves}


@router.get("/get_shelves", response_model=ReturnShelves)
def get_shelves(user_id: int = Header(None, alias="x-user-id"),
                session=Depends(get_session)):

    check_user(user_id, session)

    # формируем и отправляем запрос
    get_shelves_query = (select(Shelf.id, Shelf.name, BookmarkInShelf.title)
                         .select_from(Shelf)
                         .join(BookmarkInShelf, BookmarkInShelf.fk_shelf == Shelf.id)
                         .where(Shelf.fk_user == user_id)
                         .group_by(Shelf.id, Shelf.name, BookmarkInShelf.title))
    result = session.execute(get_shelves_query).fetchall()
    if not result:
        return {"shelves": []}

    # форматируем ответ
    response_list = []
    last_id = -1
    counter = 0
    new_shelf = {"id": -1, "name": "None", "bookmarks": []}
    for shelf in result:
        if shelf.id != last_id:
            counter = 0
            if last_id != -1:
                response_list.append(new_shelf)
            last_id = shelf.id
            new_shelf = {"id": shelf[0], "name": shelf[1], "bookmarks": []}
        if counter > 2:
            continue
        counter += 1
        new_shelf["bookmarks"].append(shelf[2])
    response_list.append(new_shelf)

    return {"shelves": response_list}


@router.get("/get_bookmarks", response_model=ReturnBookmarks)
def get_bookmarks(shelf_id: int,
                  user_id: int = Header(None, alias="x-user-id"),
                  session=Depends(get_session)):

    check_user(user_id, session)

    # формируем и отправляем запрос
    get_bookmarks_query = (select(Bookmark.id, BookmarkInShelf.title)
                           .join(BookmarkInShelf, Bookmark.id == BookmarkInShelf.fk_bookmark)
                           .where(BookmarkInShelf.fk_shelf == shelf_id))
    result = session.execute(get_bookmarks_query).fetchall()

    if not result:
        return {"bookmarks": []}

    bookmark_list = []
    for element in result:
        bookmark_list.append({"id": element.id, "title": element.title})
    return {"bookmarks": bookmark_list}


@router.post("/create_shelf", response_model=dict)
def create_shelf(shelf_name: CreateShelf,
                 user_id: int = Header(None, alias="x-user-id"),
                 session=Depends(get_session)):

    check_user(user_id, session)

    # формируем запрос
    create_shelf_query = (
        pg_insert(Shelf)
        .values(fk_user=user_id, name=shelf_name.name)
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
        select(Shelf).where(Shelf.id == new_bookmark.shelf_id)
    )
    result = session.execute(check_shelf)
    if not result:
        raise HTTPException(status_code=404, detail="Shelf not found")

    # формируем запросы
    add_bookmark_query = (
        pg_insert(Bookmark)
        .values(id=new_bookmark.bookmark_id).on_conflict_do_nothing()
    )

    add_link_query = (
        pg_insert(BookmarkInShelf)
        .values(fk_bookmark=new_bookmark.bookmark_id,
                title=new_bookmark.title,
                fk_shelf=new_bookmark.shelf_id)
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
        select(Shelf).where(Shelf.id == bookmark_to_remove.shelf_id)
    )
    result = session.execute(check_shelf)
    if not result:
        raise HTTPException(status_code=404, detail="Shelf not found")

    # формируем запрос
    remove_bookmark_query = (
        delete(BookmarkInShelf)
        .where(BookmarkInShelf.fk_bookmark == bookmark_to_remove.bookmark_id)
        .where(BookmarkInShelf.fk_shelf == bookmark_to_remove.shelf_id)
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
        select(Shelf).where(Shelf.id == shelf_to_remove.shelf_id)
    )
    result = session.execute(check_shelf)
    if not result:
        return {"message": "Nothing to remove"}

    # формируем запросы
    remove_shelf_query = (
        delete(Shelf)
        .where(Shelf.id == shelf_to_remove.shelf_id)
    )
    remove_link_query = (
        delete(BookmarkInShelf)
        .where(BookmarkInShelf.fk_shelf == shelf_to_remove.shelf_id)
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
