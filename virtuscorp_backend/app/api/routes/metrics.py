from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.utils.helpers import get_current_user
from app.models.user import User
import pandas as pd
import os
import glob
import traceback
from datetime import datetime, timezone

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
    try:
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        if not files:
            return {"data": []}

        latest_file = max(files, key=os.path.getctime)
        
        # Debug information
        print(f"Reading file: {latest_file}")
        
        if latest_file.endswith(".csv"):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
        
        # Convert to records and handle NaN values
        records = df.fillna(0).to_dict(orient="records")
        
        # Debug information
        print(f"Records count: {len(records)}")
        if len(records) > 0:
            print(f"First record keys: {list(records[0].keys())}")
        
        return {"data": records}
    except Exception as e:
        # Print full traceback for debugging
        traceback_str = traceback.format_exc()
        print(f"Error in get_uploaded_data: {str(e)}")
        print(f"Traceback: {traceback_str}")
        
        # Return a more detailed error
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to read file: {str(e)}. Please check file format and contents."
        )
