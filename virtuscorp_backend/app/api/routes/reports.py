from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.crud import crud_report
from app.utils.report_generator import generate_financial_report  # Example report generator
import os
import uuid
import traceback
from app.models.report import Report  # Import the Report model
from app.utils.helpers import get_current_user
from app.schemas.report import ReportResponse
from typing import List, Optional
import pandas as pd
import io
import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import glob

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
    # If the font is not found, we'll use the standard font


@router.post("/", response_model=ReportRead)
async def create_report(
    report_in: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create a new report.
    """
    report_in.user_id = current_user.id
    report = await crud_report.report.create(db, obj_in=report_in)
    return report


@router.get("/{report_id}", response_model=ReportRead)
async def read_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a report by ID.
    """
    report = await crud_report.report.get(db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return report


@router.put("/{report_id}", response_model=ReportRead)
async def update_report(
    report_id: int,
    report_in: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a report.
    """
    report = await crud_report.report.get(db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    report = await crud_report.report.update(db, db_obj=report, obj_in=report_in)
    return report


@router.delete("/{report_id}", response_model=ReportRead)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a report.
    """
    report = await crud_report.report.get(db, id=report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    report = await crud_report.report.remove(db, id=report_id)
    return report


@router.get("/", response_model=list[ReportRead])
async def read_reports(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10, alias="limit"),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get all reports for the current user.
    """
    reports = await crud_report.report.get_multi_by_owner(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return reports


@router.post("/reports/generate", response_class=Response)
async def generate_report(
    report_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a report based on the uploaded data and the provided report configuration.
    Returns a PDF file.
    """
    try:
        # Log the current user information for debugging
        print(f"Report generation requested by user ID: {current_user.id}, email: {current_user.email}")
        print(f"Generating report with data: {json.dumps(report_data, default=str)}")
        
        # Find the latest uploaded file for the user
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        if not files:
            raise HTTPException(
                status_code=404, 
                detail="No data file found. Please upload a file on the 'Data Sources' page first."
            )
        
        latest_file = max(files, key=os.path.getctime)
        print(f"Using file: {latest_file}")
        
        # Read the data from the file
        try:
            if latest_file.endswith(".csv"):
                df = pd.read_csv(latest_file)
            else:
                df = pd.read_excel(latest_file)
            
            # Check if the DataFrame is empty
            if df.empty:
                raise HTTPException(
                    status_code=400, 
                    detail="The data file is empty. Please upload a file with data."
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
        
        # Apply filters from the request
        if report_data.get("exclude_taxes", False):
            # Example filtering - adapt to your data structure
            if "Налоги" in df.columns:
                df = df[df["Налоги"] == 0]
                print("Applied tax exclusion filter")
        
        # Create a PDF document
        buffer = io.BytesIO()
        
        # Set up styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName='DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=16,
            spaceAfter=12
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName='DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
            fontSize=10
        )
        
        # Create the PDF document
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        report_title = f"Отчет: {report_data.get('report_type', 'Финансовая сводка')}"
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add report metadata
        if report_data.get("date_range"):
            elements.append(Paragraph(f"Период: {report_data['date_range']}", normal_style))
        
        if report_data.get("filters"):
            elements.append(Paragraph(f"Фильтры: {report_data['filters']}", normal_style))
        
        elements.append(Spacer(1, 12))
        
        # Convert DataFrame to table for PDF
        # Get headers and data
        headers = df.columns.tolist()
        data = [headers]  # First row - headers
        
        # Add data rows
        for _, row in df.iterrows():
            data.append([str(x) for x in row.tolist()])
        
        # Create table
        table = Table(data)
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans' if 'DejaVuSans' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Build the PDF
        doc.build(elements)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Generate filename and timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"{report_data.get('report_type', 'Report')}_{timestamp}.pdf"
        file_path = os.path.join(REPORTS_DIR, filename)
        
        # Save the PDF to disk
        with open(file_path, "wb") as f:
            f.write(pdf_data)
        
        # Create a record in the database for the generated report
        try:
            # Log the current user ID to verify it's being passed correctly
            print(f"Creating report with user ID: {current_user.id}")
            
            report = await Report.create(
                title=report_title,
                user=current_user,  # Pass the entire user object
                report_type=report_data.get("report_type", "financial"),
                status="completed",
                filters_applied=report_data.get("filters", ""),
                export_format=report_data.get("export_format", "pdf"),
                file_path=file_path
            )
            print(f"Created report record with ID: {report.id} for user ID: {current_user.id}")
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
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error generating report: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        # Return a user-friendly error
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating report: {str(e)}"
        )
