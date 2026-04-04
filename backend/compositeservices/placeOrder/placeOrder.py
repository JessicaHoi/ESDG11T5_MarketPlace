import os, pika, json, requests
from dotenv import load_dotenv

load_dotenv()

ORDER_URL        = os.environ.get("ORDER_SERVICE_URL")
PAYMENT_URL      = os.environ.get("PAYMENT_SERVICE_URL")
LISTING_URL      = os.environ.get("LISTING_SERVICE_URL")
MESSAGING_URL    = os.environ.get("MESSAGING_SERVICE_URL")
NOTIFICATION_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5002")
RABBITMQ_URL     = os.environ.get("RABBITMQ_URL")
SELLER_PHONE     = os.environ.get("SELLER_PHONE")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def publish_order_placed(payload: dict):
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange='order_events', exchange_type='topic', durable=True)
    ch.basic_publish(
        exchange='order_events',
        routing_key='order.placed',
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[→] Published event: order.placed")


def place_order(data: dict):
    listing_id    = data['listingID']
    buyer_id      = int(data['buyerID'])
    seller_id     = int(data['sellerID'])
    amount        = data['amount']
    listing_title = data.get('listingTitle', f'Listing #{listing_id}')
    message       = data.get('message', 'I would like to purchase this item.')

    # ---------- Step 1: Reserve the listing (OutSystems) ----------
    # TODO: Uncomment once OutSystems Listing Service URL is available
    # reserve_resp = requests.put(f"{LISTING_URL}/listing/{listing_id}/reserve", json={"status": "RESERVED"})
    # if reserve_resp.status_code != 200:
    #     return {"error": "Step 1 failed: Could not reserve listing", "details": safe_json(reserve_resp)}, 400
    print(f"[1] SKIPPED — Listing reservation bypassed. listing_id={listing_id}")

    # ---------- Step 2: Send message (best-effort) ----------
    print(f"[2] Sending message from buyer {buyer_id} to seller {seller_id}...")
    try:
        msg_resp = requests.post(
            f"{MESSAGING_URL}/messages",
            json={
                "orderID":    0,
                "senderID":   buyer_id,
                "receiverID": seller_id,
                "content":    message
            },
            timeout=10
        )
        if msg_resp.status_code != 201:
            print(f"[2] WARNING: Messaging failed ({msg_resp.status_code}): {msg_resp.text} — continuing anyway")
        else:
            print(f"[2] Message sent successfully")
    except Exception as e:
        print(f"[2] WARNING: Messaging service unreachable: {e} — continuing anyway")

    # ---------- Step 3: Create the order ----------
    print(f"[3] Creating order for '{listing_title}'...")
    order_resp = requests.post(
        f"{ORDER_URL}/orders",
        json={
            "buyerID":       buyer_id,
            "sellerID":      seller_id,
            "listingID":     listing_id,
            "amount":        amount,
            "order_details": listing_title,
        }
    )
    if order_resp.status_code != 201:
        return {"error": "Step 3 failed: Could not create order", "details": safe_json(order_resp)}, 400

    order = order_resp.json()
    order_id = order['order_id']

    # ---------- Step 4: Hold payment in escrow ----------
    print(f"[4] Holding payment in escrow for order {order_id}...")
    payment_resp = requests.post(
        f"{PAYMENT_URL}/payment/escrow",
        json={
            "orderID":         order_id,
            "amount":          amount,
            "paymentMethodID": data.get('paymentMethodID', 'pm_card_visa')
        }
    )
    if payment_resp.status_code != 201:
        return {"error": "Step 4 failed: Could not hold payment", "details": safe_json(payment_resp)}, 400

    payment = payment_resp.json()

    # ---------- Step 5: Mark listing as sold (OutSystems) ----------
    # TODO: Uncomment once OutSystems Listing Service URL is available
    print(f"[5] SKIPPED — Listing mark-as-sold bypassed. listing_id={listing_id}")

    # ---------- Step 5b: Notify seller via SMS ----------
    print(f"[5b] Notifying seller via SMS...")
    delivery_option = data.get('deliveryOption', 'meetup')
    delivery_text = 'Shipping' if delivery_option == 'shipping' else 'Self-collection / Meetup'
    sms_body = (
        f"[TradeNest] Payment received! "
        f"Buyer has paid ${amount} for '{listing_title}' (Listing #{listing_id}). "
        f"Delivery method: {delivery_text}. "
        f"Order #{order_id}. Please arrange handover with the buyer."
    )
    try:
        requests.post(
            f"{NOTIFICATION_URL}/notification",
            json={
                "orderID":       order_id,
                "notification":  sms_body,
                "receiverID":    seller_id,
                "receiverPhone": SELLER_PHONE,
            },
            timeout=10,
        )
        print(f"[5b] Seller notification sent")
    except Exception as e:
        print(f"[5b] WARNING: Could not send seller notification: {e}")

    # ---------- Step 6: Notify buyer and seller via AMQP ----------
    print(f"[6] Publishing order.placed event...")
    try:
        publish_order_placed({
            "orderID":   order_id,
            "buyerID":   buyer_id,
            "sellerID":  seller_id,
            "amount":    amount,
            "listingID": listing_id
        })
    except Exception as e:
        print(f"[6] WARNING: Could not publish AMQP event: {e} — continuing anyway")

    return {
        "message":   "Order placed successfully",
        "orderID":   order_id,
        "listingID": listing_id,
        "paymentID": payment.get('data', {}).get('paymentID'),
        "status":    "RESERVED"
    }, 201
