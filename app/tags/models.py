from datetime import datetime, timezone
from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, ForeignKey

from core.database import metadata


user_tag = Table(
    "user_tag",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fk_user", Integer, ForeignKey("user.id"), index=True),
    Column("tag", String, nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.now(timezone.utc), nullable=False),
)
