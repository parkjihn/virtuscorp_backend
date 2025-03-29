#!/bin/bash

echo "Checking for Aerich initialization..."
if [ ! -d "migrations" ]; then
    echo "Initializing Aerich..."
    aerich init -t app.db.database.TORTOISE_ORM
    aerich init-db
else
    echo "Running Aerich migrations..."
    aerich migrate
    aerich upgrade
fi

echo "Starting FastAPI app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
