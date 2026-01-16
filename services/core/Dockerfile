FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy application + migrations
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

# Миграции -> старт API
CMD ["sh","-lc","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
