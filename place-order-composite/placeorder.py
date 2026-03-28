import os, pika, json, requests
from dotenv import load_dotenv

load_dotenv()

ORDER_URL    = os.environ.get("ORDER_SERVICE_URL")
PAYMENT_URL  = os.environ.get("PAYMENT_SERVICE_URL")
LISTING_URL  = os.environ.get("LISTING_SERVICE_URL")
MESSAGING_URL = os.environ.get("MESSAGING_SERVICE_URL")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL")


def publish_order_placed(payload: dict):
    """Publish order.placed → Notification Service auto-notifies buyer & seller"""
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
    listing_id = data['listingID']
    buyer_id   = data['buyerID']
    seller_id  = data['sellerID']
    amount     = data['amount']
    message    = data.get('message', 'I would like to purchase this item.')

    # ---------- Step 1: Reserve the listing ----------
    print(f"[1] Reserving listing {listing_id}...")
    reserve_resp = requests.put(
        f"{LISTING_URL}/listing/{listing_id}/reserve",
        json={"status": "RESERVED"}
    )
    if reserve_resp.status_code != 200:
        return {
            "error": "Step 1 failed: Could not reserve listing",
            "details": reserve_resp.json()
        }, 400

    # ---------- Step 2: Send message from buyer to seller ----------
    print(f"[2] Sending message from buyer {buyer_id} to seller {seller_id}...")
    msg_resp = requests.post(
        f"{MESSAGING_URL}/messages",
        json={
            "orderID":    0,
            "senderID":   buyer_id,
            "receiverID": seller_id,
            "content":    message
        }
    )
    if msg_resp.status_code != 201:
        return {
            "error": "Step 2 failed: Could not send message",
            "details": msg_resp.json()
        }, 400

    # ---------- Step 3: Create the order ----------
    print(f"[3] Creating order...")
    order_resp = requests.post(
        f"{ORDER_URL}/orders",
        json={
            "buyerID":   buyer_id,
            "sellerID":  seller_id,
            "listingID": listing_id,
            "amount":    amount,
            "status":    "RESERVED"
        }
    )
    if order_resp.status_code != 201:
        return {
            "error": "Step 3 failed: Could not create order",
            "details": order_resp.json()
        }, 400

    order = order_resp.json()
    order_id = order['orderID']

    # ---------- Step 4: Hold payment in escrow ----------
    print(f"[4] Holding payment in escrow...")
    payment_resp = requests.post(
        f"{PAYMENT_URL}/payment/escrow",
        json={
            "orderID":    order_id,
            "amount":     amount,
            "holdStatus": "HELD"
        }
    )
    if payment_resp.status_code != 201:
        return {
            "error": "Step 4 failed: Could not hold payment",
            "details": payment_resp.json()
        }, 400

    payment = payment_resp.json()

    # ---------- Step 5: Mark listing as sold ----------
    print(f"[5] Marking listing {listing_id} as sold...")
    sold_resp = requests.put(
        f"{LISTING_URL}/listing/{listing_id}/sold",
        json={"status": "SOLD"}
    )
    if sold_resp.status_code != 200:
        return {
            "error": "Step 5 failed: Could not mark listing as sold",
            "details": sold_resp.json()
        }, 400

    # ---------- Step 6: Notify buyer and seller via AMQP ----------
    print(f"[6] Publishing order.placed event...")
    publish_order_placed({
        "orderID":   order_id,
        "buyerID":   buyer_id,
        "sellerID":  seller_id,
        "amount":    amount,
        "listingID": listing_id
    })

    return {
        "message":   "Order placed successfully",
        "orderID":   order_id,
        "listingID": listing_id,
        "paymentID": payment.get('paymentID'),
        "status":    "RESERVED"
    }, 201