from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, Request, status, Path, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory="templates")

app = FastAPI(
    title="Users CRUD example",
    summary="Пример CRUD-сервиса пользователей на FastAPI",
    description="""
API демонстрирует базовые CRUD-операции над пользователями с in-memory хранилищем.

**Особенности:**
- Валидация входных данных через Pydantic
- Уникальность `email`
- Подробные описания эндпоинтов/моделей для Swagger UI и ReDoc
""",
    version="1.0.0",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "users",
            "description": "Операции создания, получения, обновления и удаления пользователей.",
        }
    ],
)

app.mount('/static', StaticFiles(directory='static'), name='static')

# ---- Schemas ----
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


# ---- In-memory "DB" ----
users: Dict[int, User] = {}
next_id = 1


# ---- CRUD Endpoints ----

@app.post(
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
    global next_id

    if any(u.email == payload.email for u in users.values()):
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(id=next_id, name=payload.name, email=payload.email)
    users[next_id] = user
    next_id += 1
    return user


@app.get(
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


@app.get(
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


@app.put(
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


@app.delete(
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

# ---- Template Routers ----

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


@app.get("/about", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="about.html"
    )