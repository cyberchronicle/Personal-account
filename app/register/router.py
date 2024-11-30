from fastapi import APIRouter, Header, Depends, HTTPException

from app.database.connection.session import SessionLocal, get_session
from app.database.models.user import User
from app.register.schema import RegisterRequest

router = APIRouter(prefix="/register", tags=["register"])


@router.post("")
async def register_user(
        register_request: RegisterRequest,
        x_user_id: str = Header(None),
        session: SessionLocal = Depends(get_session)
):
    existing_user = session.query(User).filter(User.id == x_user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        id=x_user_id,
        login=register_request.login,
        first_name=register_request.first_name,
        last_name=register_request.last_name
    )

    session.add(new_user)
    session.commit()


# @router.get("/user-icon-get-link")
# def upload_file(file: UploadFile) -> None:
#     upload_file_to_s3(file)