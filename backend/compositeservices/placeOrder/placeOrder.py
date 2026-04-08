import os, pika, json, requests
from dotenv import load_dotenv

load_dotenv()

ORDER_URL    = os.environ.get("ORDER_SERVICE_URL")
PAYMENT_URL  = os.environ.get("PAYMENT_SERVICE_URL")
LISTING_URL  = os.environ.get("LISTING_SERVICE_URL")
RABBITMQ_URL = os.environ.get("RABBITMQ_URL")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def publish_order_placed(payload: dict):
    """Publish order.placed event to RabbitMQ — notification service handles SMS + SSE."""
    params = pika.URLParameters(RABBITMQ_URL)
    conn   = pika.BlockingConnection(params)
    ch     = conn.channel()
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
    delivery_opt  = data.get('deliveryOption', 'meetup')

    # ---------- Step 1: Reserve the listing (OutSystems) ----------
    # TODO: Uncomment once OutSystems Listing Service URL is available
    # reserve_resp = requests.put(f"{LISTING_URL}/listing/{listing_id}/reserve", json={"status": "RESERVED"})
    # if reserve_resp.status_code != 200:
    #     return {"error": "Step 1 failed: Could not reserve listing", "details": safe_json(reserve_resp)}, 400
    print(f"[1] SKIPPED — Listing reservation bypassed. listing_id={listing_id}")

    # ---------- Step 2: Create the order ----------
    print(f"[2] Creating order for '{listing_title}'...")
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
        return {"error": "Step 2 failed: Could not create order", "details": safe_json(order_resp)}, 400

    order    = order_resp.json()
    order_id = order['order_id']

    # ---------- Step 3: Hold payment in escrow ----------
    print(f"[3] Holding payment in escrow for order {order_id}...")
    payment_resp = requests.post(
        f"{PAYMENT_URL}/payment/escrow",
        json={
            "orderID":         order_id,
            "amount":          amount,
            "paymentMethodID": data.get('paymentMethodID', 'pm_card_visa')
        }
    )
    if payment_resp.status_code != 201:
        return {"error": "Step 3 failed: Could not hold payment", "details": safe_json(payment_resp)}, 400

    payment = payment_resp.json()

    # ---------- Step 4: Decrement listing quantity (OutSystems) ----------
    print(f"[4] Updating listing quantity in OutSystems for listing_id={listing_id}...")
    try:
        get_resp = requests.get(f"{LISTING_URL}{listing_id}/", timeout=10)
        if get_resp.status_code == 200:
            listing_data = get_resp.json().get('data', {})
            current_qty  = listing_data.get('listingStockQty', 0)
            new_qty      = max(0, current_qty - 1)

            put_resp = requests.put(
                f"{LISTING_URL}",
                json={
                    "listingID":          listing_data.get('listingID'),
                    "listingStatus":      listing_data.get('listingStatus', ''),
                    "listingName":        listing_data.get('listingName', ''),
                    "listingCategory":    listing_data.get('listingCategory', ''),
                    "listingPrice":       listing_data.get('listingPrice', 0),
                    "listingDescription": listing_data.get('listingDescription', ''),
                    "listingStockQty":    new_qty,
                    "listingImgUrl":      listing_data.get('listingImgUrl', ''),
                    "is_active":          listing_data.get('is_active', True),
                },
                timeout=10
            )
            if put_resp.status_code == 200:
                print(f"[4] Listing quantity updated: {current_qty} → {new_qty}")
            else:
                print(f"[4] WARNING: Failed to update quantity ({put_resp.status_code}) — continuing anyway")
        else:
            print(f"[4] WARNING: Could not fetch listing ({get_resp.status_code}) — quantity update skipped")
    except Exception as e:
        print(f"[4] WARNING: OutSystems unreachable: {e} — continuing anyway")

    # ---------- Step 5: Publish order.placed via AMQP → notification service handles SMS + SSE ----------
    # Notification service consumer (handle_order_placed) will notify both buyer and seller
    print(f"[5] Publishing order.placed event via AMQP...")
    try:
        publish_order_placed({
            "orderID":       order_id,
            "buyerID":       buyer_id,
            "sellerID":      seller_id,
            "amount":        amount,
            "listingID":     listing_id,
            "listingTitle":  listing_title,
            "deliveryOption": delivery_opt,
        })
    except Exception as e:
        print(f"[5] WARNING: Could not publish AMQP event: {e} — continuing anyway")

    return {
        "message":   "Order placed successfully",
        "orderID":   order_id,
        "listingID": listing_id,
        "paymentID": payment.get('data', {}).get('paymentID'),
        "status":    "RESERVED"
    }, 201
