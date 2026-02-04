
from typing import List
from fastapi import Body, HTTPException, Path, APIRouter, status
from schemas import ErrorResponse, User, UserCreate, UserUpdate
from database import users
import database

router = APIRouter()

@router.post(
    "/users",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
    summary="Создать пользователя",
    description="""
Создаёт нового пользователя.

**Правила:**
- `email` должен быть уникальным (иначе вернётся `400`).
- Поля валидируются Pydantic (например, формат email).
""",
    responses={
        201: {
            "description": "Пользователь создан",
            "content": {
                "application/json": {
                    "example": {"id": 1, "name": "Иван Петров", "email": "ivan.petrov@example.com"}
                }
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "Email уже существует",
            "content": {"application/json": {"example": {"detail": "Email already exists"}}},
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
def create_user(
    payload: UserCreate = Body(
        ...,
        description="Данные для создания пользователя.",
        examples={
            "basic": {
                "summary": "Обычный пользователь",
                "value": {"name": "Иван Петров", "email": "ivan.petrov@example.com"},
            }
        },
    )
):
    """Создание пользователя (in-memory)."""
    if any(u.email == payload.email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(id=database.next_id, name=payload.name, email=payload.email)
    users[database.next_id] = user
    database.next_id += 1
    return user


@router.get(
    "/users",
    response_model=List[User],
    tags=["users"],
    summary="Получить список пользователей",
    description="""
Возвращает список всех пользователей.

- Порядок соответствует порядку добавления (для текущего in-memory хранения).
""",
    responses={
        200: {
            "description": "Список пользователей",
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "name": "Иван Петров", "email": "ivan.petrov@example.com"},
                        {"id": 2, "name": "Анна Иванова", "email": "anna@example.com"},
                    ]
                }
            },
        }
    },
)
def list_users():
    """Список пользователей."""
    return list(users.values())


@router.get(
    "/users/{user_id}",
    response_model=User,
    tags=["users"],
    summary="Получить пользователя по ID",
    description="""
Возвращает одного пользователя по `user_id`.

Если пользователь не найден — вернётся `404`.
""",
    responses={
        200: {
            "description": "Пользователь найден",
            "content": {
                "application/json": {
                    "example": {"id": 1, "name": "Иван Петров", "email": "ivan.petrov@example.com"}
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Пользователь не найден",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
def get_user(
    user_id: int = Path(
        ...,
        ge=1,
        description="ID пользователя (целое число >= 1).",
        examples=[1],
    )
):
    """Получить пользователя по ID."""
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put(
    "/users/{user_id}",
    response_model=User,
    tags=["users"],
    summary="Обновить пользователя",
    description="""
Обновляет пользователя по `user_id`.

**Поведение:**
- Можно передать только часть полей (`name` и/или `email`).
- Если `email` меняется — он должен быть уникальным.
- Если пользователь не найден — `404`.
""",
    responses={
        200: {
            "description": "Пользователь обновлён",
            "content": {
                "application/json": {
                    "example": {"id": 1, "name": "Иван Петров", "email": "new.email@example.com"}
                }
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "Email уже существует",
            "content": {"application/json": {"example": {"detail": "Email already exists"}}},
        },
        404: {
            "model": ErrorResponse,
            "description": "Пользователь не найден",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
def update_user(
    user_id: int = Path(..., ge=1, description="ID пользователя для обновления.", examples=[1]),
    payload: UserUpdate = Body(
        ...,
        description="Поля для обновления. Можно передать только те, которые нужно изменить.",
        examples={
            "update_name": {"summary": "Обновить только имя", "value": {"name": "Иван Петров"}},
            "update_email": {"summary": "Обновить только email", "value": {"email": "new.email@example.com"}},
            "update_both": {
                "summary": "Обновить имя и email",
                "value": {"name": "Иван Петров", "email": "new.email@example.com"},
            },
        },
    ),
):
    """Обновить пользователя (in-memory)."""
    user = users.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_name = payload.name if payload.name is not None else user.name
    new_email = payload.email if payload.email is not None else user.email

    if new_email != user.email and any(u.email == new_email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already exists")

    updated = User(id=user_id, name=new_name, email=new_email)
    users[user_id] = updated
    return updated


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
    summary="Удалить пользователя",
    description="""
Удаляет пользователя по `user_id`.

- Если пользователь удалён успешно — `204 No Content`.
- Если пользователь не найден — `404`.
""",
    responses={
        204: {"description": "Пользователь удалён (тело ответа пустое)"},
        404: {
            "model": ErrorResponse,
            "description": "Пользователь не найден",
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
def delete_user(
    user_id: int = Path(..., ge=1, description="ID пользователя для удаления.", examples=[1])
):
    """Удалить пользователя (in-memory)."""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    del users[user_id]
    return None