# app/config.py

import os

def get_database_url():
    try:
        with open("/run/secrets/db_password", "r") as f:
            password = f.read().strip()
    except FileNotFoundError:
        password = os.getenv("DB_PASSWORD", "")

    return f"postgres://postgres:{password}@db:5432/virtuscorp_db"
