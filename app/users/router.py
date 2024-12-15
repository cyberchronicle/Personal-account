from fastapi import APIRouter, Header, Depends, HTTPException

from app.database.connection.session import SessionLocal, get_session
from app.database.models.user import User
from app.users.schema import RegisterRequest

from app.users.schema import UserDto

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register_user(
        register_request: RegisterRequest,
        user_id: int = Header(None, alias="x-user-id"),
        session: SessionLocal = Depends(get_session)
):
    """Регистрация пользователя"""
    existing_user = session.query(User).filter(User.id == user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        id=user_id,
        login=register_request.login,
        first_name=register_request.first_name,
        last_name=register_request.last_name
    )

    session.add(new_user)
    session.commit()


@router.get("/get", response_model=UserDto)
async def get_user(
        user_id: int = Header(None, alias="x-user-id"),
        session: SessionLocal = Depends(get_session)
):
    """Получение информации о пользователе"""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User is not found")

    return UserDto.from_orm(user)

