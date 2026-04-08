import pika, json, os, requests

# ── Notification service URL (for internal self-call to trigger SSE + SMS) ────
NOTIFICATION_URL = os.environ.get('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')


def _post_notification(order_id, dispute_id, receiver_id, message):
    """
    Internal HTTP call to POST /notification within the same service.
    This ensures SSE push + SMS both fire, since routes.py handles both.
    """
    try:
        requests.post(f"{NOTIFICATION_URL}/notification", json={
            "orderID":      order_id,
            "disputeID":    dispute_id,
            "notification": message,
            "receiverID":   receiver_id,
        }, timeout=10)
        print(f"[✓] Notification dispatched for user {receiver_id}: {message[:60]}...")
    except Exception as e:
        print(f"[!] Could not dispatch notification for user {receiver_id}: {e}")


# ─── Event handlers ───────────────────────────────────────────────────────────

def handle_order_placed(app, db, Notification, payload):
    """Buyer pays → notify buyer (payment confirmed) and seller (new order)."""
    order_id  = payload['orderID']
    buyer_id  = payload['buyerID']
    seller_id = payload['sellerID']
    amount    = payload.get('amount', '')
    listing   = payload.get('listingTitle', f"Listing #{payload.get('listingID', '')}")

    _post_notification(order_id, None, buyer_id,
        f"[Ouimarché] Payment confirmed! ${amount} is held in escrow for '{listing}'. Order #{order_id}.")
    _post_notification(order_id, None, seller_id,
        f"[Ouimarché] New order received! Buyer has paid ${amount} for '{listing}'. Order #{order_id}.")


def handle_message_sent(app, db, Notification, payload):
    """New chat message → notify receiver."""
    order_id    = payload['orderID']
    sender_id   = payload['senderID']
    receiver_id = payload['receiverID']
    # Use content directly — negotiate composite already composes the right message text
    content     = payload.get('content', f"New message from user {sender_id}")

    _post_notification(order_id, None, receiver_id, content)


def handle_dispute_raised(app, db, Notification, payload):
    """Dispute raised → notify seller (respond within 24hrs) and buyer (dispute filed)."""
    order_id      = payload['orderID']
    dispute_id    = payload['disputeID']
    seller_id     = payload['sellerID']
    buyer_id      = payload['buyerID']
    reason        = payload.get('disputeReason', '').replace('_', ' ')
    listing_title = payload.get('listingTitle', f"Order #{order_id}")
    amount        = payload.get('amount', '')

    _post_notification(order_id, dispute_id, seller_id,
        f"[Ouimarché] A dispute has been raised against your listing '{listing_title}' "
        f"(Order #{order_id}, Dispute #{dispute_id}). "
        f"Reason: {reason}. You have 24 hours to respond.")
    _post_notification(order_id, dispute_id, buyer_id,
        f"[Ouimarché] Your dispute on Order #{order_id} has been filed (Dispute #{dispute_id}). "
        f"The seller has 24 hours to respond.")
    # Notify admin
    _post_notification(order_id, dispute_id, 99,
        f"[Ouimarché] New dispute raised. Dispute #{dispute_id}, Order #{order_id}. "
        f"Listing: '{listing_title}', Amount: ${amount}. Reason: {reason}.")


def handle_dispute_seller_responded(app, db, Notification, payload):
    """Seller submits response → notify buyer to review, notify admin."""
    order_id      = payload['orderID']
    dispute_id    = payload['disputeID']
    buyer_id      = payload['buyerID']
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, dispute_id, buyer_id,
        f"[Ouimarché] The seller has responded to Dispute #{dispute_id} for '{listing_title}'. "
        f"Order #{order_id}. Please review their response.")
    _post_notification(order_id, dispute_id, 99,
        f"[Ouimarché] Seller has responded to Dispute #{dispute_id} for Order #{order_id}. "
        f"Awaiting further action.")


def handle_seller_agreed(app, db, Notification, payload):
    """Seller agrees to refund → notify admin to make final decision, notify buyer."""
    order_id      = payload['orderID']
    dispute_id    = payload['disputeID']
    buyer_id      = payload['buyerID']
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, dispute_id, 99,
        f"[Ouimarché] Seller has agreed on Dispute #{dispute_id}. "
        f"Admin decision required for Order #{order_id}. Please review and make a final decision.")
    _post_notification(order_id, dispute_id, buyer_id,
        f"[Ouimarché] The seller has acknowledged Dispute #{dispute_id} for '{listing_title}'. "
        f"An admin will now review and make a final decision.")


def handle_dispute_resolved(app, db, Notification, payload):
    """Admin approves dispute → notify buyer (refunded) and seller (outcome)."""
    order_id      = payload['orderID']
    dispute_id    = payload['disputeID']
    buyer_id      = payload['buyerID']
    seller_id     = payload['sellerID']
    amount        = payload.get('amount', '')
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, dispute_id, buyer_id,
        f"[Ouimarché] ✅ Dispute #{dispute_id} APPROVED. "
        f"You will be refunded ${amount} for '{listing_title}'. "
        f"Funds will be returned to your original payment method.")
    _post_notification(order_id, dispute_id, seller_id,
        f"[Ouimarché] Dispute #{dispute_id} outcome: APPROVED in buyer's favour. "
        f"Buyer has been refunded ${amount} for '{listing_title}'. Order #{order_id}.")


def handle_dispute_rejected(app, db, Notification, payload):
    """Admin rejects dispute → notify buyer (rejected) and seller (funds released)."""
    order_id      = payload['orderID']
    dispute_id    = payload['disputeID']
    buyer_id      = payload['buyerID']
    seller_id     = payload['sellerID']
    amount        = payload.get('amount', '')
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, dispute_id, buyer_id,
        f"[Ouimarché] Dispute #{dispute_id} outcome: REJECTED. "
        f"Funds of ${amount} have been released to the seller for '{listing_title}'. Order #{order_id}.")
    _post_notification(order_id, dispute_id, seller_id,
        f"[Ouimarché] ✅ Dispute #{dispute_id} REJECTED in your favour. "
        f"${amount} has been released to you for '{listing_title}'. Order #{order_id}.")


def handle_order_confirmed(app, db, Notification, payload):
    """Buyer confirms receipt → notify seller (payment released) and buyer (confirmation)."""
    order_id      = payload['orderID']
    seller_id     = payload['sellerID']
    buyer_id      = payload['buyerID']
    amount        = payload.get('amount', '')
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, None, seller_id,
        f"[Ouimarché] 🎉 Buyer confirmed receipt of '{listing_title}'. "
        f"${amount} has been released to you. Order #{order_id}.")
    _post_notification(order_id, None, buyer_id,
        f"[Ouimarché] Receipt confirmed for '{listing_title}'. "
        f"Funds have been released to the seller. Order #{order_id}.")


def handle_order_delivered(app, db, Notification, payload):
    """Seller marks item as delivered → notify buyer to confirm receipt."""
    order_id      = payload['orderID']
    buyer_id      = payload['buyerID']
    listing_title = payload.get('listingTitle', f"Order #{order_id}")

    _post_notification(order_id, None, buyer_id,
        f"[Ouimarché] Your item '{listing_title}' has been marked as delivered. "
        f"Please confirm receipt to release payment to the seller. Order #{order_id}.")


# ─── Consumer startup ─────────────────────────────────────────────────────────

def start_consumer(app, db, Notification):
    url    = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    params = pika.URLParameters(url)
    conn   = pika.BlockingConnection(params)
    ch     = conn.channel()

    # Declare all exchanges
    for exchange in ['messaging_events', 'order_events', 'dispute_events']:
        ch.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)

    result     = ch.queue_declare(queue='notification_queue', durable=True)
    queue_name = result.method.queue

    # Bind all routing keys
    bindings = [
        ('messaging_events', 'message.sent'),
        ('order_events',     'order.placed'),
        ('order_events',     'order.delivered'),   # seller marks delivered
        ('order_events',     'order.confirmed'),   # buyer confirms receipt
        ('dispute_events',   'dispute.raised'),
        ('dispute_events',   'dispute.seller_responded'),
        ('dispute_events',   'dispute.seller_agreed'),
        ('dispute_events',   'dispute.resolved'),
        ('dispute_events',   'dispute.rejected'),
    ]
    for exchange, routing_key in bindings:
        ch.queue_bind(exchange=exchange, queue=queue_name, routing_key=routing_key)

    HANDLERS = {
        'message.sent':              lambda p: handle_message_sent(app, db, Notification, p),
        'order.placed':              lambda p: handle_order_placed(app, db, Notification, p),
        'order.delivered':           lambda p: handle_order_delivered(app, db, Notification, p),
        'order.confirmed':           lambda p: handle_order_confirmed(app, db, Notification, p),
        'dispute.raised':            lambda p: handle_dispute_raised(app, db, Notification, p),
        'dispute.seller_responded':  lambda p: handle_dispute_seller_responded(app, db, Notification, p),
        'dispute.seller_agreed':     lambda p: handle_seller_agreed(app, db, Notification, p),
        'dispute.resolved':          lambda p: handle_dispute_resolved(app, db, Notification, p),
        'dispute.rejected':          lambda p: handle_dispute_rejected(app, db, Notification, p),
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
