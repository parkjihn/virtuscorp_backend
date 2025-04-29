from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReportBase(BaseModel):
    title: str
    report_type: Optional[str] = None
    filters_applied: Optional[str] = None
    export_format: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    id: int
    created_at: datetime
    status: str
    file_url: Optional[str] = None

    class Config:
        orm_mode = True

class ReportGenerateRequest(BaseModel):
    report_type: str
    date_range: Optional[str] = None
    filters: Optional[str] = None
    exclude_taxes: Optional[bool] = False
    show_profit_margin: Optional[bool] = False
    export_format: str = "pdf"
    file_naming: Optional[str] = None
    download_to_device: bool = True
    combine_reports: bool = False
