# app/api/routes/reports.py

from fastapi import APIRouter, Depends, HTTPException, Response
from app.models.user import User
from app.models.report import Report
from app.utils.helpers import get_current_user
from app.schemas.report import ReportGenerateRequest, ReportResponse
import pandas as pd
import io
import json
import os
import glob
import traceback
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
REPORTS_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Register a font with Cyrillic support
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
except Exception as e:
    print(f"Warning: Could not register DejaVuSans font: {str(e)}")

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(current_user: User = Depends(get_current_user)):
    """Get all reports for the current user."""
    reports = await Report.filter(user=current_user).all()
    return reports

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, current_user: User = Depends(get_current_user)):
    """Get a specific report by ID."""
    report = await Report.get_or_none(id=report_id, user=current_user)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.delete("/reports/{report_id}")
async def delete_report(report_id: int, current_user: User = Depends(get_current_user)):
    """Delete a report."""
    report = await Report.get_or_none(id=report_id, user=current_user)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await report.delete()
    return {"message": "Report deleted successfully"}

@router.post("/reports/generate", response_class=Response)
async def generate_report(
    report_data: ReportGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a report based on the uploaded data.
    Returns a PDF file.
    """
    try:
        # Log the current user information for debugging
        print(f"Report generation requested by user ID: {current_user.id}, email: {current_user.email}")
        
        # Find the latest uploaded file for the user
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        if not files:
            raise HTTPException(
                status_code=404, 
                detail="No data file found. Please upload a file first."
            )
        
        latest_file = max(files, key=os.path.getctime)
        print(f"Using file: {latest_file}")
        
        # Read the data from the file
        try:
            if latest_file.endswith(".csv"):
                df = pd.read_csv(latest_file)
            else:
                df = pd.read_excel(latest_file)
            
            if df.empty:
                raise HTTPException(
                    status_code=400, 
                    detail="The data file is empty."
                )
            
            print(f"Data loaded successfully. Shape: {df.shape}")
        except Exception as e:
            print(f"Error reading data file: {str(e)}")
            traceback_str = traceback.format_exc()
            print(f"Traceback: {traceback_str}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to read data file: {str(e)}"
            )
        
        # Create a PDF document
        buffer = io.BytesIO()
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        report_title = f"Отчет: {report_data.report_type}"
        elements.append(Paragraph(report_title, styles['Heading1']))
        
        # Convert DataFrame to table for PDF
        headers = df.columns.tolist()
        data = [headers]
        for _, row in df.iterrows():
            data.append([str(x) for x in row.tolist()])
        
        table = Table(data)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"{report_data.report_type}_{timestamp}.pdf"
        file_path = os.path.join(REPORTS_DIR, filename)
        
        # Save the PDF to disk
        with open(file_path, "wb") as f:
            f.write(pdf_data)
        
        # Create a record in the database - FIX FOR FOREIGN KEY ISSUE
        try:
            # Debug: Print user details to verify
            print(f"Creating report record with user ID: {current_user.id}")
            print(f"User model details: {current_user.__dict__}")
            
            # First check if the user exists in the database
            user_exists = await User.exists(id=current_user.id)
            if not user_exists:
                print(f"WARNING: User with ID {current_user.id} does not exist in the database")
                # Return the PDF without creating a record
                return Response(
                    content=pdf_data,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"'
                    }
                )
            
            # Try creating the report with user_id instead of user object
            report = await Report.create(
                title=report_title,
                user_id=current_user.id,  # Use user_id instead of user
                report_type=report_data.report_type,
                status="completed",
                filters_applied=report_data.filters or "",
                export_format=report_data.export_format,
                file_path=file_path
            )
            
            print(f"Created report record with ID: {report.id}")
        except Exception as e:
            print(f"Error creating report record: {str(e)}")
            traceback_str = traceback.format_exc()
            print(f"Traceback: {traceback_str}")
            # Continue even if the database record creation fails
        
        # Return the PDF file
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating report: {str(e)}"
        )
