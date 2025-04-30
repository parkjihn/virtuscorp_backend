from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timezone

class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255, null=True)
    position = fields.CharField(max_length=100, null=True)
    department = fields.CharField(max_length=100, null=True)
    phone = fields.CharField(max_length=20, null=True)
    avatar_url = fields.CharField(max_length=255, null=True)
    last_login = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"
    
    def __str__(self):
        return f"{self.email}"
