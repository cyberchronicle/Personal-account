from pydantic import BaseModel
from typing import List


class ReturnShelves(BaseModel):
    shelves: List[dict]


class ReturnOnlyShelves(BaseModel):
    id: List[int]


class CreateShelf(BaseModel):
    name: str


class ReturnBookmarks(BaseModel):
    bookmarks: List[dict]


class AddBookmark(BaseModel):
    bookmark_id: int
    title: str
    shelf_id: int


class RemoveBookmark(BaseModel):
    bookmark_id: int
    shelf_id: int


class RemoveShelf(BaseModel):
    shelf_id: int
