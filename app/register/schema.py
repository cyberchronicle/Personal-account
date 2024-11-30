from pydantic import BaseModel


class RegisterRequest(BaseModel):
    login: str
    first_name: str
    last_name: str
