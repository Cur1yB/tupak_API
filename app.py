from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import api, templates as template_router


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
templates = Jinja2Templates(directory="templates")
app.mount('/static', StaticFiles(directory='static'), name='static')

app.include_router(template_router.router)
app.include_router(api.router)
