from fastapi import FastAPI
from app.middleware.cors import add_cors_middleware

app = FastAPI()

add_cors_middleware(app) 

@app.get("/")
def read_root():
    return {"message": "Привет от FastAPI на проекте virtuscorp! nginx test"}
