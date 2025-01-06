from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey

from app.database.models import Base


class UserTag(Base):
    __tablename__ = "user_tags"
    __table_args__ = ({"schema": "personal_account"})

    user_id = Column(Integer, ForeignKey("personal_account.users.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("personal_account.tags.id"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False)


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = {'schema': 'personal_account'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
