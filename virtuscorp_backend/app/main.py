from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Привет от FastAPI на проекте virtuscorp! erfgergerg"}
