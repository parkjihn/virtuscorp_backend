from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.middleware.cors import add_cors_middleware
from app.api.routes import auth, yandex, metrics, reports, user
from tortoise.contrib.fastapi import register_tortoise
from app.db.database import TORTOISE_ORM
import os

app = FastAPI()

add_cors_middleware(app)

app.include_router(auth.router, prefix="/auth")
app.include_router(yandex.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")  
app.include_router(reports.router, prefix="/api")
app.include_router(user.router, prefix="/api/user")

# Mount the uploads directory for serving static files
# Create the directory if it doesn't exist
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
    
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Create uploaded_files directory if it doesn't exist
uploaded_files_dir = "uploaded_files"
if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

# Create reports directory if it doesn't exist
reports_dir = "reports"
if not os.path.exists(reports_dir):
    os.makedirs(reports_dir)

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/")
def read_root():
    return {"message": "Привет от FastAPI на проекте virtuscorp! nginx test"}
