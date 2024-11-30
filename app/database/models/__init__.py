from app.database.connection.session import engine
from app.database.models.base import Base
from app.database.models.user import User

Base.metadata.create_all(bind=engine)
