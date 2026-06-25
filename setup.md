# hub_notify — Local Setup Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 14+ | Job tracking DB (shared with hub_backend) |
| RabbitMQ | 3.12+ | Durable message queue |
| Mailpit | any | Catches emails locally without actually sending them |

The easiest way to run PostgreSQL, RabbitMQ, and Mailpit is via the Docker Compose
file in `hub_infra/`. If you don't have that, run them individually:

```bash
# PostgreSQL
docker run -d --name cixio-pg -e POSTGRES_DB=cixiohub -e POSTGRES_USER=cixiohub \
  -e POSTGRES_PASSWORD=cixiohub -p 5432:5432 postgres:16

# RabbitMQ (with management UI at http://localhost:15672)
docker run -d --name cixio-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Mailpit (SMTP at port 1025, web UI at http://localhost:8025)
docker run -d --name cixio-mailpit -p 1025:1025 -p 8025:8025 axllent/mailpit
```

---

## 1. Clone and create a virtual environment

```bash
cd hub_notify
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
DATABASE_URL=postgresql+asyncpg://cixiohub:cixiohub@localhost:5432/cixiohub
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# For local dev with Mailpit (no real credentials needed):
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM_EMAIL=noreply@cixiohub.dev
```

Twilio and Firebase credentials will be provided by the instructor.
See `.env.example` for detailed instructions on each variable.

---

## 4. Run database migrations

```bash
alembic upgrade head
```

This creates the `notification_jobs` table in the shared PostgreSQL database.

---

## 5. Start the service

```bash
uvicorn app.main:app --reload --port 8001
```

On startup the service:
- Registers all routes under `/api/v1/`
- Starts 5 asyncio background workers (file, rag, email, sms, analytics)
- Opens the RabbitMQ connection for the producer

---

## 6. Verify it's running

```bash
curl http://localhost:8001/api/v1/health
# → {"status":"ok","service":"cixiohub-notify"}
```

Open the interactive API docs:
```
http://localhost:8001/docs
```

---

## 7. Test email sending (with Mailpit)

With Mailpit running, send a test email via the API:

```bash
curl -X POST http://localhost:8001/api/v1/notify/send \
  -H "Content-Type: application/json" \
  -d '{"channel":"email","recipient":"test@example.com","subject":"Test","body":"Hello from CixioHub"}'
```

Then open **http://localhost:8025** to see the caught email in Mailpit.

---

## 8. Test the queue dashboard

Open the frontend at `http://localhost:3003/queues` — it connects to the notify
service SSE stream at `http://localhost:8001/api/v1/jobs/stream`.

Or trigger a job directly:

```bash
curl -X POST http://localhost:8001/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"job_type":"bulk_email","label":"Test Bulk","payload":{"count":10}}'
```

---

## 9. Run the RabbitMQ consumer (optional, separate process)

The asyncio workers handle in-process jobs. The RabbitMQ consumer is the durable
path for bulk notification jobs submitted via `/api/v1/notify/bulk`:

```bash
python -m app.queue.consumer
```

Run this in a separate terminal alongside `uvicorn`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `connection refused` on port 5432 | PostgreSQL is not running |
| `connection refused` on port 5672 | RabbitMQ is not running |
| Email not appearing in Mailpit | Check `SMTP_HOST=localhost` and `SMTP_PORT=1025` in `.env` |
| Push raises `NotImplementedError` | Set `FIREBASE_SERVICE_ACCOUNT_JSON` in `.env` (see `.env.example`) |
| WhatsApp raises `TwilioRestException` | Set Twilio credentials, and ensure the recipient has opted in to the sandbox |
| `alembic upgrade head` fails | Check `DATABASE_URL` in `.env` and that PostgreSQL is reachable |
