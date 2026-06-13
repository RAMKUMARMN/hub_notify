FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8001
# Run both the HTTP API (port 8001) and the queue worker via supervisord
# In development you can run them separately:
#   uvicorn app.main:app --port 8001
#   python -m app.queue.consumer
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
