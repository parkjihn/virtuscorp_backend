from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from app.utils.helpers import get_current_user
from app.models.user import User
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportResponse
from typing import List, Optional
import pandas as pd
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import glob

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Регистрируем шрифт с поддержкой кириллицы
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
except:
    # Если шрифт не найден, используем стандартный
    pass

@router.post("/reports/generate", response_class=Response)
async def generate_report(
    report_data: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        # Ищем последний загруженный файл пользователя
        files = glob.glob(f"{UPLOAD_DIR}/user_{current_user.id}_*")
        if not files:
            raise HTTPException(status_code=404, detail="Файл с данными не найден. Пожалуйста, загрузите файл на странице 'Источники данных'")
        
        latest_file = max(files, key=os.path.getctime)
        
        # Читаем данные из файла
        if latest_file.endswith(".csv"):
            df = pd.read_csv(latest_file)
        else:
            df = pd.read_excel(latest_file)
        
        # Применяем фильтры из запроса
        if report_data.get("exclude_taxes", False):
            # Пример фильтрации - в реальном приложении нужно адаптировать под структуру данных
            if "Налоги" in df.columns:
                df = df[df["Налоги"] == 0]
        
        # Создаем PDF документ
        buffer = io.BytesIO()
        
        # Настраиваем стили
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
        
        # Создаем PDF документ
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Добавляем заголовок
        report_title = f"Отчет: {report_data.get('report_type', 'Финансовая сводка')}"
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 12))
        
        # Добавляем информацию о фильтрах
        if report_data.get("date_range"):
            elements.append(Paragraph(f"Период: {report_data['date_range']}", normal_style))
        
        if report_data.get("filters"):
            elements.append(Paragraph(f"Фильтры: {report_data['filters']}", normal_style))
        
        elements.append(Spacer(1, 12))
        
        # Преобразуем DataFrame в таблицу для PDF
        # Получаем заголовки и данные
        headers = df.columns.tolist()
        data = [headers]  # Первая строка - заголовки
        
        # Добавляем строки данных
        for _, row in df.iterrows():
            data.append([str(x) for x in row.tolist()])
        
        # Создаем таблицу
        table = Table(data)
        
        # Стилизуем таблицу
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
        
        # Строим PDF
        doc.build(elements)
        
        # Получаем содержимое буфера
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Создаем запись в базе данных о сгенерированном отчете
        report = await Report.create(
            title=report_title,
            user=current_user,
            report_type=report_data.get("report_type", "financial"),
            status="completed",
            filters_applied=report_data.get("filters", ""),
            export_format=report_data.get("export_format", "pdf")
        )
        
        # Формируем имя файла
        filename = f"{report_data.get('report_type', 'Report')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Возвращаем PDF файл
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании отчета: {str(e)}")

@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(current_user: User = Depends(get_current_user)):
    """Получить список отчетов пользователя"""
    reports = await Report.filter(user=current_user).order_by("-created_at")
    return reports

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, current_user: User = Depends(get_current_user)):
    """Получить конкретный отчет по ID"""
    report = await Report.get_or_none(id=report_id, user=current_user)
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    return report
