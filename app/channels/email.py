import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"  
SMTP_PORT = 587                  # Modern standard submission port
SENDER_EMAIL = "karthiksaj.05@gmail.com"  
SENDER_PASSWORD = "azxs ttbt lujh bwlb"       

def send_real_otp(recipient_email, otp_code):
    """
    Connects to the real SMTP server using STARTTLS on port 587 and delivers an OTP.
    """
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #1a73e8;">CixioHub Authentication Step</h2>
        <p>Hello,</p>
        <p>Your one-time verification password (OTP) is highly confidential:</p>
        <div style="background: #f1f3f4; padding: 10px; font-size: 24px; font-weight: bold; letter-spacing: 2px;">
          {otp_code}
        </div>
        <p>This validation token is valid for a limited window. Do not share this code.</p>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "CixioHub Secure Verification Code"
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context()
    
    try:
        # Step 1: Establish a standard unencrypted connection first
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.ehlo() 
            
            # Step 2: Upgrade the connection to a secure encrypted SSL/TLS session
            server.starttls(context=context) 
            server.ehlo()
            
            # Step 3: Login and dispatch
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, message.as_string())
            
        print(f" [✓] Real email successfully sent to {recipient_email}")
        return True
    except Exception as e:
        print(f" [X] SMTP Delivery Failure: {e}")
        return False