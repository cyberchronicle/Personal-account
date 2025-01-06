from sqlalchemy import MetaData, text
from sqlalchemy.orm import declarative_base

from app.database.connection.session import engine

with engine.connect() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS personal_account;"))
metadata = MetaData(schema="personal_account")
Base = declarative_base(metadata=metadata)

