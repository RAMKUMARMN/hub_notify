import pika
import json
import sys
from email import send_real_otp

def process_queue_message(ch, method, properties, body):
    print("\n[->] Consumer picked up a task from 'email.process' queue...", flush=True)
    
    try:
        # Decode the structural payload message dropped by the producer
        payload = json.loads(body.decode())
        email = payload.get("email")
        otp = payload.get("otp")
        
        # Trigger the actual delivery logic
        success = send_real_otp(recipient_email=email, otp_code=otp)
        
        if success:
            # Tell RabbitMQ the message was successfully completely processed
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(" [✓] Task finished cleanly. Acknowledged to RabbitMQ.", flush=True)
        else:
            print(" [X] Worker failed delivery. Keeping message in queue.", flush=True)
            
    except Exception as e:
        print(f" [X] Runtime decoding issue: {e}", flush=True)
        
    print("\n[*] Status: ONLINE & IDLE. Listening to 'email.process'...", end="", flush=True)

def start_worker():
    # Establish network connection with your running Docker container broker
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    
    # Module 5 requirement: Ensure the specific 'email.process' queue exists and is durable [cite: 1]
    channel.queue_declare(queue='email.process', durable=True)
    
    # Listen continuously to the target stream [cite: 1]
    channel.basic_consume(queue='email.process', on_message_callback=process_queue_message)
    
    print("\n==========================================================")
    print("[*] Cixio Notification Microservice Engine Online.")
    print("[*] Status: ONLINE & IDLE. Listening to 'email.process'...")
    print("==========================================================", end="", flush=True)
    
    channel.start_consuming()

if __name__ == '__main__':
    try:
        start_worker()
    except KeyboardInterrupt:
        print('\n[!] Microservice shutting down.')
        sys.exit(0)