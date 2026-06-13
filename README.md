# Notify — CixioHub Notification Service

Standalone Python/FastAPI microservice that handles all outbound notifications: Email, SMS, Push, and WhatsApp. Consumes tasks from RabbitMQ queues and dispatches them via the appropriate provider.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.11+** | Language |
| **FastAPI** | HTTP API (single-send + job status endpoints) |
| **aio-pika** | Async RabbitMQ client |
| **smtplib / aiosmtplib** | SMTP email sending |
| **twilio** | SMS + WhatsApp |
| **firebase-admin** | FCM push notifications (Android) |
| **boto3** | AWS SNS (APNs push for iOS) |
| **SQLAlchemy** | Job tracking in PostgreSQL |

---

## Project Structure

```
notify/
├── app/
│   ├── main.py              # FastAPI app for the HTTP API
│   ├── config.py            # Settings from env vars
│   ├── database.py          # SQLAlchemy session (shared with backend DB)
│   │
│   ├── channels/            # One file per notification channel
│   │   ├── __init__.py
│   │   ├── email.py         # SMTP / AWS SES sender
│   │   ├── sms.py           # Twilio SMS
│   │   ├── push.py          # Firebase FCM (Android) + AWS SNS APNs (iOS)
│   │   └── whatsapp.py      # Twilio WhatsApp API
│   │
│   ├── queue/
│   │   ├── __init__.py
│   │   ├── producer.py      # Publish messages to RabbitMQ (called by backend)
│   │   ├── consumer.py      # Async workers — consume + dispatch
│   │   └── schemas.py       # Pydantic models for queue message payloads
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── notify.py        # /notify/send, /notify/bulk, /notify/jobs/*
│   │
│   └── models/
│       └── job.py           # NotificationJob SQLAlchemy model
│
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Setup & Running

### 1. Prerequisites
- RabbitMQ running (from `infra/` Docker Compose)
- PostgreSQL running (shared with backend)
- SMTP credentials, Twilio credentials, Firebase service account key

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in SMTP, Twilio, Firebase, AWS SNS values
```

### 4. Run the HTTP API

```bash
uvicorn app.main:app --reload --port 8001
```

### 5. Run the queue worker (separate process)

```bash
python -m app.queue.worker
# This starts async consumers for email.process, sms.process, push.process
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string, e.g., `postgresql://user:password@localhost/mydatabase` |
| `RABBITMQ_URL` | RabbitMQ connection string, e.g., `amqp://user:password@localhost:5672/` |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP port (587 for TLS) |
| `SMTP_USERNAME` | SMTP username / email |
| `SMTP_PASSWORD` | SMTP password |
| `SMTP_FROM_EMAIL` | Sender address shown to recipients |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Twilio SMS sending number |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp-enabled number |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase admin SDK JSON (base64 encoded) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for SNS |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_REGION` | AWS region |
| `SNS_PLATFORM_ARN_IOS` | AWS SNS platform application ARN for APNs |
| `MAX_RETRY_ATTEMPTS` | Max retries before moving to failed queue (default: 4) |

---

## API Endpoints

### POST `/api/v1/notify/send`
Send a single notification immediately.

Request body:
```json
{
  "channel": "email",
  "recipient": "student@tkmce.ac.in",
  "subject": "Welcome to CixioHub",
  "body": "Your account has been created. Temp password: abc123XYZ",
  "html_body": "<h1>Welcome</h1><p>Temp password: <b>abc123XYZ</b></p>"
}
```

For SMS:
```json
{
  "channel": "sms",
  "recipient": "+919876543210",
  "body": "Your CixioHub temp password is: abc123XYZ"
}
```

For Push:
```json
{
  "channel": "push",
  "recipient": "fcm_device_token_here",
  "title": "New response",
  "body": "CixioHub finished generating your answer.",
  "data": { "session_id": "uuid" }
}
```

Response `200`:
```json
{ "status": "sent", "message_id": "twilio_or_smtp_id" }
```

---

### POST `/api/v1/notify/bulk`
Enqueue a bulk notification job.

Request body:
```json
{
  "channel": "email",
  "recipients": [
    {
      "recipient": "user1@tkmce.ac.in",
      "subject": "Your credentials",
      "body": "Password: abc111"
    },
    {
      "recipient": "user2@tkmce.ac.in",
      "subject": "Your credentials",
      "body": "Password: xyz222"
    }
  ]
}
```

Response `202`:
```json
{ "job_id": "uuid", "total": 2, "status": "queued" }
```

---

### GET `/api/v1/notify/jobs/{job_id}`
Get progress of a bulk job.

Response:
```json
{
  "job_id": "uuid",
  "channel": "email",
  "total": 1000,
  "sent": 893,
  "failed": 12,
  "retrying": 95,
  "completed": false,
  "updated_at": "2026-05-23T11:30:00Z"
}
```

---

## Queue Architecture

### Queues in RabbitMQ

```
email.process  ──(fail)──▶  email.retry  ──(max retries)──▶  email.failed
sms.process    ──(fail)──▶  sms.retry    ──(max retries)──▶  sms.failed
push.process   ──(fail)──▶  push.retry   ──(max retries)──▶  push.failed
```

### Message Format (JSON payload in each queue message)

```json
{
  "job_id": "uuid",
  "channel": "email",
  "recipient": "student@tkmce.ac.in",
  "subject": "Welcome",
  "body": "...",
  "attempt": 1,
  "max_attempts": 4
}
```

### Worker Logic (pseudocode)

```python
async def process_message(message):
    payload = json.loads(message.body)
    try:
        await dispatch(payload)          # call email/sms/push channel
        await message.ack()
        await update_job(payload["job_id"], sent=+1)
    except Exception:
        if payload["attempt"] >= payload["max_attempts"]:
            await message.ack()
            await publish(f"{channel}.failed", payload)
            await update_job(payload["job_id"], failed=+1)
        else:
            await message.nack(requeue=False)
            payload["attempt"] += 1
            await publish_with_delay(f"{channel}.retry", payload, delay_seconds=retry_delay(payload["attempt"]))
            await update_job(payload["job_id"], retrying=+1)
```

### Retry Delays

| Attempt | Delay before retry |
|---------|--------------------|
| 2nd | 1 minute |
| 3rd | 5 minutes |
| 4th | 30 minutes |
| After 4th | Moved to `*.failed` |

---

## Channel Implementation Notes

### Email (SMTP)
```python
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

async def send_email(to: str, subject: str, body: str, html: str = None):
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    if html:
        msg.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        use_tls=True,
    )
```

### SMS (Twilio)
```python
from twilio.rest import Client

def send_sms(to: str, body: str):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to
    )
    return message.sid
```

### Push (FCM)
```python
import firebase_admin
from firebase_admin import messaging

def send_push(device_token: str, title: str, body: str, data: dict = None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=device_token,
    )
    response = messaging.send(message)
    return response
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start both the HTTP API and the queue worker via a process manager
RUN pip install supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8001
CMD ["/usr/bin/supervisord"]
```

---

## Related Repositories

