FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install flask gunicorn

# Команда для запуска
CMD ["python", "app.py"]