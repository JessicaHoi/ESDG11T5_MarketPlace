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
    """Buyer pays → notify buyer + seller."""
    order_id  = payload['orderID']
    buyer_id  = payload['buyerID']
    seller_id = payload['sellerID']
    amount    = payload.get('amount', '')
    listing   = payload.get('listingTitle', f"Listing #{payload.get('listingID', '')}")

    notify(app, db, Notification, buyer_id, order_id,
           f"[TradeNest] Payment confirmed! ${amount} is held in escrow for '{listing}'. "
           f"Order #{order_id}. We'll notify you when the seller ships.")

    notify(app, db, Notification, seller_id, order_id,
           f"[TradeNest] New order received! Buyer has paid ${amount} for '{listing}'. "
           f"Order #{order_id}. Please arrange delivery with the buyer.")


def handle_message_sent(app, db, Notification, payload):
    """New chat message → notify receiver."""
    order_id   = payload['orderID']
    sender_id  = payload['senderID']
    receiver_id = payload['receiverID']
    content    = payload.get('content', '')[:80]

    notify(app, db, Notification, receiver_id, order_id,
           f"[TradeNest] New message from user {sender_id}: {content}")


def handle_dispute_raised(app, db, Notification, payload):
    """Dispute raised → notify seller to respond within 24 hrs."""
    order_id   = payload['orderID']
    dispute_id = payload['disputeID']
    seller_id  = payload['sellerID']
    buyer_id   = payload['buyerID']
    reason     = payload.get('disputeReason', '').replace('_', ' ')

    notify(app, db, Notification, seller_id, order_id,
           f"[TradeNest] ⚠ Dispute raised on Order #{order_id}. "
           f"Reason: {reason}. You have 24 hours to respond. "
           f"Dispute ID: {dispute_id}.",
           dispute_id=dispute_id)

    notify(app, db, Notification, buyer_id, order_id,
           f"[TradeNest] Your dispute on Order #{order_id} has been filed. "
           f"The seller has 24 hours to respond. Dispute ID: {dispute_id}.",
           dispute_id=dispute_id)


def handle_receipt_confirmed(app, db, Notification, payload):
    """Buyer confirms receipt → notify seller funds are released."""
    order_id  = payload['orderID']
    seller_id = payload['sellerID']
    buyer_id  = payload['buyerID']
    amount    = payload.get('amount', '')
    listing   = payload.get('listingTitle', f"Order #{order_id}")

    notify(app, db, Notification, seller_id, order_id,
           f"[TradeNest] 🎉 Payment released! Buyer confirmed receipt of '{listing}'. "
           f"${amount} has been released to you. Order #{order_id}.")

    notify(app, db, Notification, buyer_id, order_id,
           f"[TradeNest] Receipt confirmed for '{listing}'. "
           f"Funds have been released to the seller. Thank you! Order #{order_id}.")


def handle_dispute_resolved(app, db, Notification, payload):
    """Admin approves dispute → buyer refunded."""
    order_id   = payload['orderID']
    dispute_id = payload['disputeID']
    buyer_id   = payload['buyerID']
    seller_id  = payload['sellerID']
    amount     = payload.get('amount', '')
    listing    = payload.get('listingTitle', f"Order #{order_id}")

    notify(app, db, Notification, buyer_id, order_id,
           f"[TradeNest] ✅ Dispute #{dispute_id} APPROVED. "
           f"You will be refunded ${amount} for '{listing}'. Order #{order_id}.",
           dispute_id=dispute_id)

    notify(app, db, Notification, seller_id, order_id,
           f"[TradeNest] Dispute #{dispute_id} was decided in the buyer's favour. "
           f"Funds of ${amount} have been returned to the buyer. Order #{order_id}.",
           dispute_id=dispute_id)


def handle_dispute_rejected(app, db, Notification, payload):
    """Admin rejects dispute → seller gets funds."""
    order_id   = payload['orderID']
    dispute_id = payload['disputeID']
    buyer_id   = payload['buyerID']
    seller_id  = payload['sellerID']
    amount     = payload.get('amount', '')
    listing    = payload.get('listingTitle', f"Order #{order_id}")

    notify(app, db, Notification, seller_id, order_id,
           f"[TradeNest] ✅ Dispute #{dispute_id} REJECTED in your favour. "
           f"${amount} has been released to you for '{listing}'. Order #{order_id}.",
           dispute_id=dispute_id)

    notify(app, db, Notification, buyer_id, order_id,
           f"[TradeNest] Dispute #{dispute_id} was not upheld. "
           f"Funds have been released to the seller. Order #{order_id}.",
           dispute_id=dispute_id)


def handle_seller_agreed(app, db, Notification, payload):
    """Seller clicks Agreement Received → notify admin."""
    order_id   = payload['orderID']
    dispute_id = payload['disputeID']
    admin_id   = 99

    notify(app, db, Notification, admin_id, order_id,
           f"[TradeNest] 🔔 Admin action required. Seller has acknowledged Dispute #{dispute_id} "
           f"on Order #{order_id}. Please review and make a final decision.",
           dispute_id=dispute_id)


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
