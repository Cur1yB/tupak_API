from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import app

router = APIRouter()

@router.get("/", response_class=HTMLResponse, summary="Главная страница",
    description="""
Возвращает список всех пользователей.

- Порядок соответствует порядку добавления (для текущего in-memory хранения).
""",)
async def read_item(request: Request):
    return app.templates.TemplateResponse(
        request=request, name="index.html"
    )


@router.get("/about", response_class=HTMLResponse)
async def read_item(request: Request):
    return app.templates.TemplateResponse(
        request=request, name="about.html"
    )