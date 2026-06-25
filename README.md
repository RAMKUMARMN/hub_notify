# hub_notify — CixioHub Notification Service

Standalone FastAPI microservice that handles all outbound notifications: Email, SMS, Push, and WhatsApp. Runs asyncio background workers that pick up jobs from in-process queues (and RabbitMQ for durability) and dispatch them through the appropriate provider.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.11+** | Language |
| **FastAPI** | HTTP API — single-send, bulk enqueue, job status, SSE dashboard stream |
| **aiosmtplib** | Async SMTP email delivery |
| **twilio** | SMS and WhatsApp |
| **firebase-admin** | FCM push notifications (Android + iOS via FlutterFire) |
| **boto3** | AWS SNS — APNs direct path for iOS (optional) |
| **aio-pika** | Async RabbitMQ client for durable bulk-job queues |
| **SQLAlchemy (async)** | Job progress tracking in PostgreSQL |

---

## Project Structure

```
hub_notify/
├── app/
│   ├── main.py              # FastAPI app — starts all 5 workers at startup
│   ├── config.py            # Settings loaded from .env via pydantic-settings
│   ├── database.py          # Async SQLAlchemy engine + session factory
│   │
│   ├── channels/            # One file per notification provider
│   │   ├── email.py         # aiosmtplib SMTP sender (async)
│   │   ├── sms.py           # Twilio SMS
│   │   ├── push.py          # Firebase FCM (Android + iOS via FlutterFire)
│   │   └── whatsapp.py      # Twilio WhatsApp API
│   │
│   ├── workers/             # Asyncio background workers (one per queue)
│   │   ├── file_worker.py   # file.uploads — simulate large file storage pipeline
│   │   ├── rag_worker.py    # rag.bulk_ingest — PDF extract → embed → ChromaDB
│   │   ├── email_worker.py  # notify.bulk_email — bulk email dispatch
│   │   ├── sms_worker.py    # notify.bulk_sms — bulk SMS via Twilio
│   │   └── analytics_worker.py  # analytics.events — engagement analysis
│   │
│   ├── queue/
│   │   ├── producer.py      # Publish tasks to RabbitMQ (called by notify router)
│   │   ├── consumer.py      # RabbitMQ consumer — durable retry path
│   │   ├── job_store.py     # In-memory job store + SSE broadcaster
│   │   └── schemas.py       # Pydantic models: Job, JobType, NotifyPayload
│   │
│   ├── routers/
│   │   ├── notify.py        # /notify/send, /notify/bulk, /notify/jobs/{id}
│   │   └── jobs.py          # /jobs/submit, /jobs/stream (SSE), /jobs/stats, /jobs/recent
│   │
│   └── models/
│       └── job.py           # NotificationJob SQLAlchemy model
│
├── alembic/                 # DB migrations
├── requirements.txt
├── Dockerfile
├── .env.example             # Copy to .env and fill in credentials
└── setup.md                 # Step-by-step local setup guide
```

---

## How It Works

### Two processing paths

**1. Demo / dashboard path** (`/api/v1/jobs/submit`)
```
HTTP POST /jobs/submit
    → jobs.py router creates a Job object
    → calls worker.enqueue(job)          # puts it in asyncio.Queue
    → worker._process() runs in the background
    → job_store.update() at each step    # broadcasts SSE events
    → /jobs/stream SSE → frontend dashboard updates in real-time
```

**2. Bulk notification path** (`/api/v1/notify/bulk`)
```
HTTP POST /notify/bulk
    → notify.py router creates NotificationJob in DB
    → producer.publish() puts each recipient into RabbitMQ
    → consumer.py worker picks up messages
    → dispatches via channels/email.py, sms.py, push.py, or whatsapp.py
    → DB job counts updated on success/failure/retry
```

### Queue names

| Queue | Worker | Provider |
|-------|--------|----------|
| `file.uploads` | file_worker | MinIO / S3 (simulated) |
| `rag.bulk_ingest` | rag_worker | ChromaDB (simulated) |
| `notify.bulk_email` | email_worker | SMTP via aiosmtplib |
| `notify.bulk_sms` | sms_worker | Twilio SMS |
| `analytics.events` | analytics_worker | Analytics DB (simulated) |
| `email.process` | consumer.py | SMTP (RabbitMQ durable path) |
| `sms.process` | consumer.py | Twilio (RabbitMQ durable path) |
| `push.process` | consumer.py | Firebase FCM (RabbitMQ durable path) |

---

## Setup & Running

See **`setup.md`** for the full step-by-step guide.

Quick start:
```bash
cp .env.example .env          # fill in credentials
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Check the service is running:
```
GET http://localhost:8001/api/v1/health
→ { "status": "ok", "service": "cixiohub-notify" }
```

---

## API Endpoints

### `GET /api/v1/health`
Health check — returns `{ "status": "ok" }`.

---

### `POST /api/v1/notify/send`
Send a single notification immediately (no queue).

```json
// Email
{ "channel": "email", "recipient": "student@tkmce.ac.in",
  "subject": "Welcome to CixioHub", "body": "Temp password: abc123" }

// SMS
{ "channel": "sms", "recipient": "+919876543210",
  "body": "Your CixioHub temp password: abc123" }

// Push
{ "channel": "push", "recipient": "<fcm_device_token>",
  "title": "New answer ready", "body": "CixioHub has finished generating your response.",
  "data": { "session_id": "uuid" } }

// WhatsApp
{ "channel": "whatsapp", "recipient": "+60123456789", "body": "Hello from CixioHub!" }
```

Response `200`: `{ "status": "sent", "message_id": "..." }`

---

### `POST /api/v1/notify/bulk`
Enqueue a bulk notification job. Returns immediately with a `job_id`.

```json
{
  "channel": "email",
  "recipients": [
    { "recipient": "user1@tkmce.ac.in", "subject": "Your credentials", "body": "Password: abc111" },
    { "recipient": "user2@tkmce.ac.in", "subject": "Your credentials", "body": "Password: xyz222" }
  ]
}
```
Response `202`: `{ "job_id": "uuid", "total": 2, "status": "queued" }`

---

### `GET /api/v1/notify/jobs/{job_id}`
Poll progress of a bulk job.

```json
{ "job_id": "uuid", "channel": "email", "status": "processing",
  "total": 100, "sent": 63, "failed": 2, "updated_at": "..." }
```

---

### `POST /api/v1/jobs/submit`
Submit a demo job to the dashboard queue system.

```json
{ "job_type": "bulk_email", "label": "Weekly Digest", "payload": { "count": 50 } }
```
Job types: `file_upload`, `rag_bulk_ingest`, `bulk_email`, `bulk_sms`, `analytics`

---

### `GET /api/v1/jobs/stream`
Server-Sent Events stream for the real-time queue dashboard.

```javascript
const es = new EventSource('http://localhost:8001/api/v1/jobs/stream');
es.onmessage = e => {
    const { event, data } = JSON.parse(e.data);
    // event: "job.queued" | "job.processing" | "job.done" | "job.failed" | "ping"
    // data: Job object with progress, message, done_count, etc.
};
```

---

### `GET /api/v1/jobs/stats`
Snapshot of per-queue counts (queued / processing / done / failed / total).

### `GET /api/v1/jobs/recent?limit=60`
Most recent jobs across all queues.

---

## Retry Logic (RabbitMQ consumer path)

| Attempt | Delay before retry |
|---------|--------------------|
| 2nd | immediate |
| 3rd | 60 seconds |
| 4th | 5 minutes |
| After 4th | Moved to `*.failed` queue |

Configured via `MAX_RETRY_ATTEMPTS` in `.env` (default: 4).

---

## Environment Variables

See `.env.example` for descriptions and setup instructions for each variable.

| Variable | Required | Default |
|----------|----------|---------|
| `DATABASE_URL` | Yes | postgresql+asyncpg://cixiohub:cixiohub@localhost:5432/cixiohub |
| `RABBITMQ_URL` | Yes | amqp://guest:guest@localhost:5672/ |
| `SMTP_HOST` | Yes | localhost |
| `SMTP_PORT` | Yes | 1025 |
| `SMTP_USERNAME` | No | (empty = no auth) |
| `SMTP_PASSWORD` | No | (empty = no auth) |
| `SMTP_FROM_EMAIL` | Yes | noreply@cixiohub.dev |
| `TWILIO_ACCOUNT_SID` | For SMS/WhatsApp | — |
| `TWILIO_AUTH_TOKEN` | For SMS/WhatsApp | — |
| `TWILIO_PHONE_NUMBER` | For SMS | — |
| `TWILIO_WHATSAPP_NUMBER` | For WhatsApp | whatsapp:+14155238886 |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | For Push | — |
| `AWS_ACCESS_KEY_ID` | For iOS APNs (optional) | — |
| `SNS_PLATFORM_ARN_IOS` | For iOS APNs (optional) | — |
| `MAX_RETRY_ATTEMPTS` | No | 4 |
