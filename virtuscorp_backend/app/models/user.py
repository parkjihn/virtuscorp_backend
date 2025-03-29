from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    full_name = fields.CharField(max_length=255)
    hashed_password = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    language = fields.CharField(max_length=20, default="ru")
    timezone = fields.CharField(max_length=50, default="UTC+3")
    theme = fields.CharField(max_length=10, default="dark")
    profile_picture = fields.CharField(max_length=500, null=True)
    is_active = fields.BooleanField(default=True)