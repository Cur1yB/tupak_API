from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import app
from routers import api


templates = Jinja2Templates(directory="templates")
app.mount('/static', StaticFiles(directory='static'), name='static')

app.app.include_router(templates.router)
app.app.include_router(api.router)