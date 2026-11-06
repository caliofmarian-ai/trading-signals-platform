FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY apps/signals_app/requirements.txt /app/app-requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/app-requirements.txt
COPY send /app/send
COPY apps/signals_app /app/apps/signals_app
ENV PYTHONUNBUFFERED=1 SIGNALS_APP_DATA_DIR=/app-data
CMD ["python", "-m", "apps.signals_app", "serve"]
