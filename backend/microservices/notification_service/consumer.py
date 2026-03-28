import pika, json, os

def handle_message_sent(app, db, Notification, payload):
    """Notify receiver when a new message arrives."""
    with app.app_context():
        note = Notification(
            orderID=payload['orderID'],
            notification=f"New message from user {payload['senderID']}: {payload['content']}",
            receiverID=payload['receiverID'],
        )
        db.session.add(note)
        db.session.commit()
        print(f"[✓] Notification created for message {payload['messageID']}")

def handle_dispute_raised(app, db, Notification, payload):
    """Notify seller to respond within 48 hours when dispute is raised."""
    with app.app_context():
        note = Notification(
            orderID=payload['orderID'],
            disputeID=payload['disputeID'],
            notification=f"A dispute has been raised. Please respond within 48 hours. Reason: {payload.get('disputeReason', '')}",
            receiverID=payload['sellerID'],
        )
        db.session.add(note)
        db.session.commit()
        print(f"[✓] Dispute notification sent to seller {payload['sellerID']}")

def handle_order_placed(app, db, Notification, payload):
    """Notify both buyer and seller when order is placed."""
    with app.app_context():
        for receiver_key, msg in [
            ('buyerID',  'Your order has been placed successfully.'),
            ('sellerID', 'You have received a new order.'),
        ]:
            note = Notification(
                orderID=payload['orderID'],
                notification=msg,
                receiverID=payload[receiver_key],
            )
            db.session.add(note)
        db.session.commit()
        print(f"[✓] Order notifications sent for order {payload['orderID']}")

def start_consumer(app, db, Notification):
    url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Declare both exchanges to listen to
    for exchange in ['messaging_events', 'order_events', 'dispute_events']:
        ch.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)

    result = ch.queue_declare(queue='notification_queue', durable=True)
    queue_name = result.method.queue

    # Bind to all relevant events
    ch.queue_bind(exchange='messaging_events', queue=queue_name, routing_key='message.sent')
    ch.queue_bind(exchange='order_events',     queue=queue_name, routing_key='order.placed')
    ch.queue_bind(exchange='dispute_events',   queue=queue_name, routing_key='dispute.raised')

    HANDLERS = {
        'message.sent':   lambda p: handle_message_sent(app, db, Notification, p),
        'order.placed':   lambda p: handle_order_placed(app, db, Notification, p),
        'dispute.raised': lambda p: handle_dispute_raised(app, db, Notification, p),
    }

    def callback(ch, method, properties, body):
        event = method.routing_key
        payload = json.loads(body)
        print(f"[←] Received event: {event}")
        handler = HANDLERS.get(event)
        if handler:
            handler(payload)

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print('[*] Notification consumer waiting for events...')
    ch.start_consuming()