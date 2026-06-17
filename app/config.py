from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database (shared with backend)
    database_url: str = "postgresql+asyncpg://cixiohub:cixiohub@localhost:5432/cixiohub"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    max_retry_attempts: int = 4

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@cixiohub.com"

    # Twilio (SMS + WhatsApp)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"

    # Firebase (Push — Android)
    firebase_service_account_json: str = ""  # base64-encoded JSON

    # AWS SNS (Push — iOS APNs)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    sns_platform_arn_ios: str = ""

    # AI Service
    ai_service_url: str = "http://localhost:8003"


settings = Settings()
