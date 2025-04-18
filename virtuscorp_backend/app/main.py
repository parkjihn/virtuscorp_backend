from fastapi import FastAPI
from app.middleware.cors import add_cors_middleware
from app.api.routes import auth
from app.api.routes import yandex  # добавлено
from tortoise.contrib.fastapi import register_tortoise
from app.db.database import TORTOISE_ORM

app = FastAPI()

add_cors_middleware(app)

app.include_router(auth.router, prefix="/auth")
app.include_router(yandex.router, prefix="/api")  # добавлено

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.get("/")
def read_root():
    return {"message": "Привет от FastAPI на проекте virtuscorp! nginx test"}
