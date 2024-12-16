from app.database.connection.session import engine
from app.database.models.base import Base
from app.database.models.user import User
from app.database.models.tag import Tag
from app.database.models.tag import UserTag
from app.database.models.bookmark import Shelf
from app.database.models.bookmark import Bookmark
from app.database.models.bookmark import BookmarkInShelf

Base.metadata.create_all(bind=engine)
