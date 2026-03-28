import pika, json, os

def publish_event(event_type: str, payload: dict):
    url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='messaging_events', exchange_type='topic', durable=True)
    ch.basic_publish(
        exchange='messaging_events',
        routing_key=event_type,       # e.g. "message.sent"
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[→] Published event: {event_type}")