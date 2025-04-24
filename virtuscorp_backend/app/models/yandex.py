from tortoise import fields
from tortoise.models import Model
from app.models.user import User

class YandexIntegration(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="yandex_integrations")
    campaign_id = fields.CharField(max_length=50)
    business_id = fields.CharField(max_length=50)
    token = fields.TextField()

    class Meta:
        table = "yandex_integrations"

    def __str__(self):
        return f"Yandex for {self.user.email}"

