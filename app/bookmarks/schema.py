from pydantic import BaseModel
from typing import List


class ReturnShelves(BaseModel):
    id: int
    name: str
    bookmarks_names: List[str]


class CreateShelf(BaseModel):
    name: str


class ReturnBookmarks(BaseModel):
    bookmark_id: int
    bookmark_name: str


class AddBookmark(BaseModel):
    bookmark_id: int
    title: str
    shelf_id: int


class RemoveBookmark(BaseModel):
    bookmark_id: int
    shelf_id: int


class RemoveShelf(BaseModel):
    shelf_id: int
