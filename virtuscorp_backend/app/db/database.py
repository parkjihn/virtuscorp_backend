from app.config import get_database_url

TORTOISE_ORM = {
    "connections": {"default": get_database_url()},
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "app.models.metric",
                "app.models.report",
                "app.models.yandex",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
