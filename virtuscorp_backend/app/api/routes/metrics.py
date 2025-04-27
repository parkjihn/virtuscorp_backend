from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from app.utils.helpers import get_current_user
from app.models.user import User
import pandas as pd
import os
import glob
import logging

# Set up logging correctly
logger = logging.getLogger(name)  # Use name instead of name

router = APIRouter(tags=["metrics"])
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-metrics")
async def upload_metrics_file(request: Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Received file upload request for {file.filename} from user {current_user.id}")
        
        if not file.filename.endswith((".csv", ".xlsx")):
            logger.warning(f"Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format")

        file_path = os.path.join(UPLOAD_DIR, f"user_{current_user.id}_{file.filename}")
        logger.info(f"Saving file to {file_path}")
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
            
        logger.info(f"File {file.filename} uploaded successfully")
        return {"message": "File uploaded successfully", "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/uploaded-data")
async def get_uploaded_data(current_user: User = Depends(get_current_user)):
    try:
        logger.info(f"Getting uploaded data for user {current_user.id}")
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        
        if not files:
            logger.info("No files found for user")
            return {"data": []}

        latest_file = max(files, key=os.path.getctime)
        logger.info(f"Reading file: {latest_file}")

        if latest_file.endswith(".csv"):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
            
        logger.info(f"Successfully processed file with {len(df)} rows")
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")