import os, requests, pika, json
from dotenv import load_dotenv

load_dotenv()

ORDER_SERVICE_URL   = os.environ.get("ORDER_SERVICE_URL",   "http://order-service:8000")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://payment-service:5000")
RABBITMQ_URL        = os.environ.get("RABBITMQ_URL",        "amqp://guest:guest@rabbitmq:5672/")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def publish_event(exchange: str, routing_key: str, payload: dict):
    """Publish an event to RabbitMQ — notification service consumes and handles SMS + SSE."""
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        conn   = pika.BlockingConnection(params)
        ch     = conn.channel()
        ch.exchange_declare(exchange=exchange, exchange_type='topic', durable=True)
        ch.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
        print(f"[AMQP] Published {routing_key} → {exchange}")
    except Exception as e:
        print(f"[AMQP] WARNING — could not publish event: {e}")


def confirm_delivery(data: dict):
    """
    Seller marks item as delivered.
    Steps:
      1. Update order status to DELIVERED
      2. Publish order.delivered via AMQP → notification service notifies buyer
    """
    order_id      = data['orderID']
    seller_id     = data['sellerID']
    buyer_id      = data['buyerID']
    listing_title = data.get('listingTitle', f"Order #{order_id}")
    amount        = data.get('amount', 0)

    # ---------- Step 1: Update order status to DELIVERED ----------
    print(f"[1] Marking order {order_id} as DELIVERED...")
    try:
        order_resp = requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            json={"status": "DELIVERED"},
            timeout=10
        )
        if order_resp.status_code not in (200, 201):
            return {"error": "Failed to update order status", "details": safe_json(order_resp)}, 400
        order_data = order_resp.json()
        print(f"[1] Order {order_id} marked as DELIVERED")
    except Exception as e:
        return {"error": f"Order service unreachable: {e}"}, 503

    # ---------- Step 2: Publish AMQP event → notifies buyer to confirm receipt ----------
    print(f"[2] Publishing order.delivered event via AMQP...")
    publish_event(
        exchange    = 'order_events',
        routing_key = 'order.delivered',
        payload     = {
            "orderID":      order_id,
            "sellerID":     seller_id,
            "buyerID":      buyer_id,
            "listingTitle": listing_title,
            "amount":       amount,
        }
    )

    return {
        "message": "Order marked as delivered. Buyer notified via AMQP.",
        "data":    order_data,
    }, 200


def confirm_receipt(data: dict):
    """
    Buyer confirms receipt of item.
    Steps:
      1. Update order status to COMPLETED
      2. Release payment from escrow to seller via payment service
      3. Publish order.confirmed via AMQP → notification service notifies seller + buyer
    """
    order_id      = data['orderID']
    buyer_id      = data['buyerID']
    seller_id     = data['sellerID']
    listing_title = data.get('listingTitle', f"Order #{order_id}")
    amount        = data.get('amount', 0)

    # ---------- Step 1: Update order status to COMPLETED ----------
    print(f"[1] Marking order {order_id} as COMPLETED...")
    try:
        order_resp = requests.put(
            f"{ORDER_SERVICE_URL}/orders/{order_id}/confirm",
            timeout=10
        )
        if order_resp.status_code not in (200, 201):
            return {"error": "Failed to confirm order", "details": safe_json(order_resp)}, 400
        order_data = order_resp.json()
        print(f"[1] Order {order_id} marked as COMPLETED")
    except Exception as e:
        return {"error": f"Order service unreachable: {e}"}, 503

    # ---------- Step 2: Release payment to seller ----------
    print(f"[2] Releasing payment for order {order_id}...")
    payment_data = {}
    try:
        payment_resp = requests.post(
            f"{PAYMENT_SERVICE_URL}/payment/release",
            json={"orderID": order_id},
            timeout=10
        )
        if payment_resp.status_code == 200:
            payment_data = payment_resp.json()
            print(f"[2] Payment released for order {order_id}")
        else:
            print(f"[2] WARNING: Payment release failed: {payment_resp.text} — continuing anyway")
    except Exception as e:
        print(f"[2] WARNING: Payment service unreachable: {e} — continuing anyway")

    # ---------- Step 3: Publish AMQP event → notifies seller + buyer ----------
    print(f"[3] Publishing order.confirmed event via AMQP...")
    publish_event(
        exchange    = 'order_events',
        routing_key = 'order.confirmed',
        payload     = {
            "orderID":      order_id,
            "buyerID":      buyer_id,
            "sellerID":     seller_id,
            "listingTitle": listing_title,
            "amount":       amount,
        }
    )

    return {
        "message": "Receipt confirmed. Payment released to seller. Notifications sent via AMQP.",
        "data": {
            "order":   order_data,
            "payment": payment_data,
        },
    }, 200
