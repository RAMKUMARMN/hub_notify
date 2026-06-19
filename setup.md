# CixioHub Notification Service (Notify) Setup Guide

This guide provides step-by-step instructions for configuring, running, and testing the CixioHub Notification Service.

---

## 1. Prerequisites

Before running the notification service, make sure you have the following installed and running:
- **Python 3.11+**
- **PostgreSQL**: A database instance (shared with the main backend)
- **RabbitMQ**: Message broker for processing notification queues (runs on default port `5672`)
- **Credentials**: SMTP server details, Twilio Account SID/Token, Firebase service account key (for Push), AWS credentials (for APNs iOS Push).

---

## 2. Local Setup & Installation

### Step 1: Create and Activate Virtual Environment
```bash
# Navigate to the notify service directory
cd hub_notify

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 3. Environment Configuration

Copy the example environment file and configure the values:
```bash
cp .env.example .env
```

Open the `.env` file and populate the following values:

| Configuration Group | Key | Description / Example |
| :--- | :--- | :--- |
| **Database** | `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/mydatabase` |
| **RabbitMQ** | `RABBITMQ_URL` | `amqp://user:password@localhost:5672/` |
| | `MAX_RETRY_ATTEMPTS` | `4` (maximum retry attempts before permanently failing) |
| **Email (SMTP)** | `SMTP_HOST` | e.g. `smtp.gmail.com` |
| | `SMTP_PORT` | `587` |
| | `SMTP_USERNAME` | Your SMTP username / email address |
| | `SMTP_PASSWORD` | Your SMTP password or App Password |
| | `SMTP_FROM_EMAIL` | Sender address visible to recipients |
| **Twilio (SMS/WA)**| `TWILIO_ACCOUNT_SID`| Twilio Account SID |
| | `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| | `TWILIO_PHONE_NUMBER`| Twilio SMS sending phone number |
| | `TWILIO_WHATSAPP_NUMBER`| Twilio WhatsApp sender number (default `whatsapp:+14155238886`) |
| **Firebase (Push)** | `FIREBASE_SERVICE_ACCOUNT_JSON` | Base64-encoded string of the Firebase service account JSON |
| **AWS (APNs iOS)** | `AWS_ACCESS_KEY_ID` | AWS IAM access key ID |
| | `AWS_SECRET_ACCESS_KEY`| AWS IAM secret access key |
| | `AWS_REGION` | AWS Region (e.g. `us-east-1`) |
| | `SNS_PLATFORM_ARN_IOS`| AWS SNS Platform application ARN |
| **JWT Config** | `JWT_SECRET_KEY` | Shared backend JWT secret key |
| | `JWT_ALGORITHM` | `HS256` |

> [!TIP]
> To base64-encode your Firebase Service Account JSON, run:
> `base64 -i service-account.json` (macOS) or `base64 -w 0 service-account.json` (Linux) and paste the output string.

---

## 4. Running the Service

The notification service consists of two main parts: the **FastAPI HTTP API** (for submitting notifications and fetching job status) and the **Queue Workers** (which consume tasks from RabbitMQ and dispatch them).

### A. Run the FastAPI HTTP API
Start the FastAPI server on port `8001`:
```bash
uvicorn app.main:app --reload --port 8001
```

> [!NOTE]
> On startup, the service lifespan automatically checks and initializes the database tables:
> - `notification_jobs`: Tracks overall job progress.
> - `individual_notifications`: Tracks each individual recipient's status and attempt count.

### B. Run the Queue Workers & Scheduler
The background workers run within the same application lifecycle. However, you can also spawn them standalone or run them concurrently using the background process executor. 
In production or supervisor setup:
```bash
python -m app.queue.worker
```

---

## 5. API Usage & testing

### Health Check
Verify the API is running and successfully connected to the database:
```bash
curl -i http://localhost:8001/api/v1/health
```

### Send a Single Notification
Submit an immediate notification. Requires a valid JWT bearer token.
```bash
curl -X POST http://localhost:8001/api/v1/notify/send \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipient": "student@tkmce.ac.in",
    "subject": "Welcome to CixioHub",
    "body": "Your account has been created successfully.",
    "html_body": "<h3>Welcome to CixioHub!</h3><p>Your account is ready.</p>"
  }'
```

### Send a Bulk Notification Job
Enqueue a bulk job to multiple recipients:
```bash
curl -X POST http://localhost:8001/api/v1/notify/bulk \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "recipients": [
      {
        "recipient": "user1@tkmce.ac.in",
        "subject": "System Update",
        "body": "Hi User 1, the system will undergo maintenance tonight."
      },
      {
        "recipient": "user2@tkmce.ac.in",
        "subject": "System Update",
        "body": "Hi User 2, the system will undergo maintenance tonight."
      }
    ]
  }'
```

### Get Bulk Job Status
Retrieve the progress details and recipient dispatch status for a specific `job_id`:
```bash
curl http://localhost:8001/api/v1/notify/jobs/<JOB_ID>
```

---

## 6. Queue & Retry Architecture

The RabbitMQ integration utilizes Dead Letter Exchanges (DLX) to automatically handle retries:
1. **Main Process Queues**: `email.process`, `sms.process`, and `push.process`.
2. **Retry Queues**: If a message fails, it is moved to a retry queue with a specific time-to-live (TTL) depending on the attempt number:
   - `<channel>.retry.60s` (TTL: 1 minute)
   - `<channel>.retry.300s` (TTL: 5 minutes)
   - `<channel>.retry.1800s` (TTL: 30 minutes)
3. **DLX Routing**: When the TTL expires on the retry queue, RabbitMQ automatically dead-letters the message back to the main processing queue (`<channel>.process`) for another try.
4. **Failed Queue**: If a message fails after `MAX_RETRY_ATTEMPTS` (default: 4), it is routed to `<channel>.failed` for logging and manual inspection.
