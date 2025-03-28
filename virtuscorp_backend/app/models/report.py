from tortoise import fields
from tortoise.models import Model
from app.models.user import User


class Report(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)  # Название отчета
    created_at = fields.DatetimeField(auto_now_add=True)
    user = fields.ForeignKeyField("models.User", related_name="reports")
    report_type = fields.CharField(max_length=100, null=True)  # "financial", "sales", "marketing" и т.п.
    file_url = fields.CharField(max_length=500, null=True)     # ссылка на файл, если экспортирован
    status = fields.CharField(max_length=50, default="in-progress")  # статус: completed / in-progress / failed
    filters_applied = fields.TextField(null=True)  # JSON или строковое описание фильтров
    export_format = fields.CharField(max_length=20, null=True)  # PDF, Excel, CSV и т.д.

    class Meta:
        table = "reports"

    def __str__(self):
        return f"{self.title} ({self.status})"
