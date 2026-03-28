FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e ".[server]"

EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
