from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Модель для создания пользователя."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Иван Петров"],
        description="Отображаемое имя пользователя.",
    )
    email: EmailStr = Field(
        ...,
        examples=["ivan.petrov@example.com"],
        description="Email пользователя. Должен быть уникальным.",
    )

class UserUpdate(BaseModel):
    """Модель для частичного обновления пользователя (необязательные поля)."""
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        examples=["Иван Петров"],
        description="Новое имя пользователя (если нужно обновить).",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        examples=["new.email@example.com"],
        description="Новый email пользователя (если нужно обновить). Должен быть уникальным.",
    )

class User(BaseModel):
    """Модель пользователя (то, что возвращает API)."""
    id: int = Field(
        ...,
        ge=1,
        examples=[1],
        description="Уникальный идентификатор пользователя.",
    )
    name: str = Field(
        ...,
        examples=["Иван Петров"],
        description="Имя пользователя.",
    )
    email: EmailStr = Field(
        ...,
        examples=["ivan.petrov@example.com"],
        description="Email пользователя.",
    )

class ErrorResponse(BaseModel):
    """Единый формат ошибки для документации (пример)."""
    detail: str = Field(..., examples=["User not found"])