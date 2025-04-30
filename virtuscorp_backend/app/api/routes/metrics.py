from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.utils.helpers import get_current_user
from app.models.user import User
import pandas as pd
import os
import glob
import traceback
from datetime import datetime, timezone
import json

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-metrics")
async def upload_metrics_file(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    """
    Upload a metrics file (CSV or Excel) for the current user.
    The file will be saved to the uploaded_files directory with a user-specific prefix.
    """
    # Validate file format
    if not file.filename.endswith((".csv", ".xlsx")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Only CSV and Excel files are supported.")

    try:
        # Create a user-specific filename to avoid conflicts
        file_path = os.path.join(UPLOAD_DIR, f"user_{current_user.id}_{file.filename}")
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Try to read the file to validate it
        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Check if the file has data
            if df.empty:
                raise HTTPException(status_code=400, detail="The uploaded file is empty.")
            
            # Log success
            print(f"Successfully uploaded and validated file: {file_path}")
            print(f"File contains {len(df)} rows and {len(df.columns)} columns")
            print(f"Columns: {list(df.columns)}")
            
        except Exception as e:
            # If we can't read the file, it's probably invalid
            os.remove(file_path)  # Clean up the invalid file
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file format or content: {str(e)}"
            )
        
        return {"message": "File uploaded successfully", "filename": file.filename}
    
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in upload_metrics_file: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        # Return a user-friendly error
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/uploaded-data")
async def get_uploaded_data(current_user: User = Depends(get_current_user)):
    """
    Get the data from the most recently uploaded file for the current user.
    Returns the data as a list of records.
    """
    try:
        # Find all files uploaded by this user
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        
        if not files:
            # No files found, return empty data
            print(f"No files found for user {current_user.id}")
            return {"data": []}

        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        # Debug information
        print(f"Reading file: {latest_file}")
        
        # Read the file based on its extension
        if latest_file.endswith(".csv"):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
        
        # Convert DataFrame to records
        # Handle NaN values by replacing them with 0
        # Also convert all values to appropriate Python types
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                # Handle NaN, NaT, and None values
                if pd.isna(value):
                    record[col] = 0
                # Handle datetime objects
                elif isinstance(value, pd.Timestamp):
                    record[col] = value.strftime("%Y-%m-%d")
                # Handle other types
                else:
                    record[col] = value
            records.append(record)
        
        # Debug information
        print(f"Records count: {len(records)}")
        if len(records) > 0:
            print(f"First record keys: {list(records[0].keys())}")
            print(f"First record sample: {json.dumps(records[0], default=str)[:200]}...")
        
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
