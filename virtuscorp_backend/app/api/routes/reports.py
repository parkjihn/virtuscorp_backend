from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from app.utils.helpers import get_current_user
from app.models.user import User
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import os
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
import traceback

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
            report = await Report.create(
                title=report_title,
                user=current_user,
                report_type=report_data.get("report_type", "financial"),
                status="completed",
                filters_applied=report_data.get("filters", ""),
                export_format=report_data.get("export_format", "pdf"),
                file_path=file_path
            )
            print(f"Created report record with ID: {report.id}")
        except Exception as e:
            print(f"Error creating report record: {str(e)}")
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

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(current_user: User = Depends(get_current_user)):
    """Get a list of reports for the current user"""
    try:
        reports = await Report.filter(user=current_user).order_by("-created_at")
        return reports
    except Exception as e:
        print(f"Error getting reports: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving reports: {str(e)}"
        )

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, current_user: User = Depends(get_current_user)):
    """Get a specific report by ID"""
    report = await Report.get_or_none(id=report_id, user=current_user)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/reports/{report_id}/download")
async def download_report(report_id: int, current_user: User = Depends(get_current_user)):
    """Download a specific report by ID"""
    try:
        # Get the report from the database
        report = await Report.get_or_none(id=report_id, user=current_user)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Check if the report has a file path
        if not hasattr(report, 'file_path') or not report.file_path or not os.path.exists(report.file_path):
            # If no file exists, regenerate the report
            # This is a simplified version - in a real app, you'd use the original parameters
            print(f"Report file not found at {getattr(report, 'file_path', 'None')}, regenerating...")
            
            # Find the latest uploaded file for the user
            files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
            if not files:
                raise HTTPException(status_code=404, detail="No data file found to regenerate report")
            
            latest_file = max(files, key=os.path.getctime)
            
            # Read the data
            if latest_file.endswith(".csv"):
                df = pd.read_csv(latest_file)
            else:
                df = pd.read_excel(latest_file)
            
            # Generate a new PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            title_style = styles["Heading1"]
            elements.append(Paragraph(report.title, title_style))
            
            # Add data as table
            headers = df.columns.tolist()
            data = [headers]
            for _, row in df.iterrows():
                data.append([str(x) for x in row.tolist()])
            
            table = Table(data)
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            table.setStyle(table_style)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Generate a new filename and save it
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"regenerated_report_{report_id}_{timestamp}.pdf"
            file_path = os.path.join(REPORTS_DIR, filename)
            
            # Save the regenerated file
            with open(file_path, "wb") as f:
                f.write(pdf_data)
            
            # Update the report record with the new file path
            report.file_path = file_path
            await report.save()
            
            # Return the regenerated PDF
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
        
        # If the file exists, read it and return it
        with open(report.file_path, "rb") as f:
            file_content = f.read()
        
        # Get the filename from the path
        filename = os.path.basename(report.file_path)
        
        # Return the file
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        print(f"Error downloading report: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading report: {str(e)}"
        )
