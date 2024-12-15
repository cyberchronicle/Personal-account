from pydantic import BaseModel


class RegisterRequest(BaseModel):
    login: str
    first_name: str
    last_name: str


class UserDto(BaseModel):
    login: str
    first_name: str
    last_name: str

    class Config:
        from_attributes=True
