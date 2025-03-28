#!/bin/bash

echo "Running Aerich migrations..."
aerich upgrade

echo "Starting FastAPI app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
