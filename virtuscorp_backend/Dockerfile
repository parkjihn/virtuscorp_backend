# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости системы (если нужно работать с asyncpg)
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем aerich и зависимости для pyproject.toml
RUN pip install aerich tomli tomlkit

# Копируем весь исходный код приложения
COPY . .

# Копируем entrypoint.sh и даём права на выполнение
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Используем entrypoint
CMD ["/app/entrypoint.sh"]
