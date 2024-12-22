from sqlalchemy import Column, Integer, String, ForeignKey

from app.database.models import Base


class Shelf(Base):
    __tablename__ = 'shelf'
    __table_args__ = ({"schema": "personal_account"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    fk_user = Column(Integer, ForeignKey('personal_account.users.id'), nullable=False)
    name = Column(String)


class Bookmark(Base):
    __tablename__ = 'bookmarks'
    __table_args__ = ({"schema": "personal_account"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)


class BookmarkInShelf(Base):
    __tablename__ = 'bookmarks_inshelf'
    __table_args__ = ({"schema": "personal_account"})
    fk_shelf = Column(Integer, ForeignKey('personal_account.shelf.id', onupdate='CASCADE', ondelete='CASCADE'),
                      primary_key=True, nullable=False)
    fk_bookmark = Column(Integer, ForeignKey('personal_account.bookmarks.id', onupdate='CASCADE', ondelete='CASCADE'),
                         primary_key=True, nullable=False)
