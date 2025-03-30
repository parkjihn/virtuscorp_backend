from fastapi import FastAPI
from app.middleware.cors import add_cors_middleware
from app.api.routes import auth 

app = FastAPI()

add_cors_middleware(app)

app.include_router(auth.router, prefix="/auth")

@app.get("/")
def read_root():
    return {"message": "Привет от FastAPI на проекте virtuscorp! nginx test"}
