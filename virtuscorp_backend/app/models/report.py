from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone

class Report(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    user = fields.ForeignKeyField("models.User", related_name="reports")
    created_at = fields.DatetimeField(auto_now_add=True)
    report_type = fields.CharField(max_length=50, default="financial")  # financial, sales, inventory, marketing
    status = fields.CharField(max_length=20, default="completed")  # completed, in-progress, failed
    filters_applied = fields.TextField(default="")
    export_format = fields.CharField(max_length=10, default="pdf")  # pdf, excel, csv, json
    file_path = fields.CharField(max_length=255, null=True)  # Path to the saved report file
    
    class Meta:
        table = "reports"
    
    def __str__(self):
        return f"{self.title} ({self.created_at})"
