FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

RUN python -m pip install --no-cache-dir --upgrade pip

COPY requirements.txt ./
COPY app ./app

RUN python -m pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
