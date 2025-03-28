from tortoise import fields
from tortoise.models import Model
from app.models.user import User


class Metric(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)  # Название метрики, например "Объем продаж"
    value = fields.FloatField()              # Значение метрики
    timestamp = fields.DatetimeField(auto_now_add=True)  # Когда зафиксировано значение
    user = fields.ForeignKeyField("models.User", related_name="metrics")  # Кто загрузил метрику
    marketplace = fields.CharField(max_length=100, null=True)  # Ozon, WB, Yandex и т.п.
    category = fields.CharField(max_length=100, null=True)     # например, "Продажи", "Ценообразование"

    class Meta:
        table = "metrics"

    def __str__(self):
        return f"{self.name}: {self.value} ({self.timestamp})"
