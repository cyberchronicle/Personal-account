from sqlalchemy import Column, Integer, String

from app.database.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
