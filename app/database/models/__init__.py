from app.database.connection.session import engine
from app.database.models.base import Base
from app.database.models.user import User
from app.database.models.tag import Tag
from app.database.models.tag import UserTag

Base.metadata.create_all(bind=engine)
