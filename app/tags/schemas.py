from pydantic import BaseModel
from typing import List


class TagsInput(BaseModel):
    """Схема для добавления тегов пользователя."""
    tags: List[str]

class TagsOutput(BaseModel):
    """Схема для получения тегов пользователя."""
    tags: List[str]