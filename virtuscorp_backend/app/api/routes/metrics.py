from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.utils.helpers import get_current_user
from app.models.user import User
import pandas as pd
import os
import glob

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-metrics")
async def upload_metrics_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    file_path = os.path.join(UPLOAD_DIR, f"user_{current_user.id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {"message": "File uploaded successfully", "filename": file.filename}

@router.get("/uploaded-data")
async def get_uploaded_data(current_user: User = Depends(get_current_user)):
    files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
    if not files:
        return {"data": []}

    latest_file = max(files, key=os.path.getctime)

    try:
        if latest_file.endswith(".csv"):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    return {"data": df.to_dict(orient="records")}
