from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    full_name = fields.CharField(max_length=255)
    hashed_password = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    position = fields.CharField(max_length=255, null=True)
    department = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=50, null=True)
    avatar_url = fields.CharField(max_length=500, null=True)
    last_login = fields.DatetimeField(null=True)
