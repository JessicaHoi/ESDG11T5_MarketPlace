import pika, json, os
from twilio_client import send_sms

# ─── Phone number lookup ──────────────────────────────────────────────────────
# Maps userID → phone number.
# In production this would come from a user service DB.
# For demo, we use env vars so they can be set per deployment without code changes.
PHONE_MAP = {
    1:  os.environ.get("BUYER_PHONE",  ""),   # Mark Foo (buyer)
    2:  os.environ.get("SELLER_PHONE", ""),   # Ryan T. (seller)
    99: os.environ.get("ADMIN_PHONE",  ""),   # Admin
}

def get_phone(user_id: int) -> str:
    """Return the phone number for a given user ID, or empty string if unknown."""
    return PHONE_MAP.get(int(user_id), "")


def notify(app, db, Notification, receiver_id: int, order_id: int, message: str, dispute_id: int = None):
    """Save notification to DB and send SMS if phone number is known."""
    with app.app_context():
        note = Notification(
            orderID=order_id,
            disputeID=dispute_id,
            notification=message,
            receiverID=receiver_id,
        )
        db.session.add(note)
        db.session.commit()
        print(f"[✓] Notification saved for user {receiver_id}: {message[:60]}...")

    # Send SMS
    phone = get_phone(receiver_id)
    if phone:
        try:
            send_sms(to_number=phone, message=message)
        except Exception as e:
            print(f"[!] SMS failed for user {receiver_id} ({phone}): {e}")
    else:
        print(f"[!] No phone number for user {receiver_id} — SMS skipped")


# ─── Event handlers ───────────────────────────────────────────────────────────

def handle_order_placed(app, db, Notification, payload):
    """Buyer pays → save notifications only (SMS handled by placeOrder composite service)."""
    order_id  = payload['orderID']
    buyer_id  = payload['buyerID']
    seller_id = payload['sellerID']
    amount    = payload.get('amount', '')
    listing   = payload.get('listingTitle', f"Listing #{payload.get('listingID', '')}")

    # Save to DB only — no SMS (placeOrder already sends SMS to seller)
    with app.app_context():
        for receiver_id, message in [
            (buyer_id,  f"[Ouimarché] Payment confirmed! ${amount} is held in escrow for '{listing}'. Order #{order_id}."),
            (seller_id, f"[Ouimarché] New order received! Buyer has paid ${amount} for '{listing}'. Order #{order_id}."),
        ]:
            note = Notification(orderID=order_id, disputeID=None, notification=message, receiverID=receiver_id)
            db.session.add(note)
        db.session.commit()
        print(f"[✓] Order placed notifications saved (no duplicate SMS)")


def handle_message_sent(app, db, Notification, payload):
    """New chat message → delegate to /notification so SSE and optional SMS are handled centrally."""
    order_id    = payload['orderID']
    sender_id   = payload['senderID']
    receiver_id = payload['receiverID']
    content     = payload.get('content', '')[:80]

    is_first = bool(payload.get('isFirst', False))
    listing_name = payload.get('listingName', '')
    listing_price = payload.get('listingPrice', '')

    if is_first and listing_name:
        message = (
            f"[Ouimarché] User #{sender_id} is interested in '{listing_name}' "
            f"(${listing_price}). They have started a negotiation chat."
        )
    else:
        message = f"[Ouimarché] New message from user {sender_id}: {content}"

    # Use notification HTTP endpoint so one codepath handles DB write + SSE push + Twilio.
    import requests as req
    notification_url = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')
    notif_payload = {
        "orderID": order_id,
        "disputeID": None,
        "notification": message,
        "receiverID": receiver_id,
    }
    if is_first:
        phone = get_phone(receiver_id)
        if phone:
            notif_payload["receiverPhone"] = phone

    try:
        req.post(f"{notification_url}/notification", json=notif_payload, timeout=10)
        print(f"[✓] Message notification handled for user {receiver_id} via /notification")
    except Exception as e:
        print(f"[!] Could not notify user {receiver_id} for message.sent: {e}")


def handle_dispute_raised(app, db, Notification, payload):
    """Dispute raised → save notifications only (SMS handled by raiseDispute composite service)."""
    order_id   = payload['orderID']
    dispute_id = payload['disputeID']
    seller_id  = payload['sellerID']
    buyer_id   = payload['buyerID']
    reason     = payload.get('disputeReason', '').replace('_', ' ')

    # Save to DB only — no SMS (raiseDispute already sends SMS)
    with app.app_context():
        for receiver_id, message in [
            (seller_id, f"[Ouimarché] Dispute raised on Order #{order_id}. Reason: {reason}. Dispute #{dispute_id}."),
            (buyer_id,  f"[Ouimarché] Your dispute on Order #{order_id} has been filed. Dispute #{dispute_id}."),
        ]:
            note = Notification(orderID=order_id, disputeID=dispute_id, notification=message, receiverID=receiver_id)
            db.session.add(note)
        db.session.commit()
        print(f"[✓] Dispute raised notifications saved (no duplicate SMS)")


def handle_receipt_confirmed(app, db, Notification, payload):
    """Buyer confirms receipt → notify seller via SMS + SSE."""
    order_id  = payload['orderID']
    seller_id = payload['sellerID']
    buyer_id  = payload['buyerID']
    amount    = payload.get('amount', '')
    listing   = payload.get('listingTitle', f"Order #{order_id}")

    # Use HTTP call to notification service so SSE push fires too
    import requests as req
    notification_url = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')
    for receiver_id, phone_key, message in [
        (seller_id, 'SELLER_PHONE', f"[Ouimarché] 🎉 Buyer confirmed receipt of '{listing}'. ${amount} released to you. Order #{order_id}."),
        (buyer_id,  'BUYER_PHONE',  f"[Ouimarché] Receipt confirmed for '{listing}'. Funds released to seller. Order #{order_id}."),
    ]:
        try:
            req.post(f"{notification_url}/notification", json={
                "orderID":       order_id,
                "notification":  message,
                "receiverID":    receiver_id,
                "receiverPhone": os.environ.get(phone_key),
            }, timeout=10)
        except Exception as e:
            print(f"[!] Could not notify user {receiver_id}: {e}")


def handle_dispute_resolved(app, db, Notification, payload):
    """Admin approves dispute → save DB only (raiseDispute composite sends SMS+SSE)."""
    pass  # raiseDispute.py resolve_dispute handles notifications


def handle_dispute_rejected(app, db, Notification, payload):
    """Admin rejects dispute → save DB only (raiseDispute composite sends SMS+SSE)."""
    pass  # raiseDispute.py reject_dispute handles notifications


def handle_seller_agreed(app, db, Notification, payload):
    """Seller clicks Agreement Received → save DB only (raiseDispute composite sends SMS+SSE)."""
    pass  # raiseDispute.py seller_agree handles notifications


# ─── Consumer startup ─────────────────────────────────────────────────────────

def start_consumer(app, db, Notification):
    url    = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    params = pika.URLParameters(url)
    conn   = pika.BlockingConnection(params)
    ch     = conn.channel()

    for exchange in ['messaging_events', 'order_events', 'dispute_events']:
        ch.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)

    result     = ch.queue_declare(queue='notification_queue', durable=True)
    queue_name = result.method.queue

    # Bind to all relevant routing keys
    bindings = [
        ('messaging_events', 'message.sent'),
        ('order_events',     'order.placed'),
        ('order_events',     'order.confirmed'),   # buyer confirms receipt
        ('dispute_events',   'dispute.raised'),
        ('dispute_events',   'dispute.resolved'),
        ('dispute_events',   'dispute.rejected'),
        ('dispute_events',   'dispute.seller_agreed'),
    ]
    for exchange, routing_key in bindings:
        ch.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

    HANDLERS = {
        'message.sent':          lambda p: handle_message_sent(app, db, Notification, p),
        'order.placed':          lambda p: handle_order_placed(app, db, Notification, p),
        'order.confirmed':       lambda p: handle_receipt_confirmed(app, db, Notification, p),
        'dispute.raised':        lambda p: handle_dispute_raised(app, db, Notification, p),
        'dispute.resolved':      lambda p: handle_dispute_resolved(app, db, Notification, p),
        'dispute.rejected':      lambda p: handle_dispute_rejected(app, db, Notification, p),
        'dispute.seller_agreed': lambda p: handle_seller_agreed(app, db, Notification, p),
    }

    def callback(ch, method, properties, body):
        event   = method.routing_key
        payload = json.loads(body)
        print(f"[←] Received event: {event}")
        handler = HANDLERS.get(event)
        if handler:
            handler(payload)
        else:
            print(f"[!] No handler for event: {event}")

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print('[*] Notification consumer waiting for events...')
    ch.start_consuming()
