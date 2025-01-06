from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, TIMESTAMP

from app.database.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = ({"schema": "personal_account"})
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False)
