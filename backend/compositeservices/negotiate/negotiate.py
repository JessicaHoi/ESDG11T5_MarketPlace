import os, json, requests, pika
from dotenv import load_dotenv

load_dotenv()

MESSAGING_URL    = os.environ.get("MESSAGING_SERVICE_URL", "http://messaging-service:5003")


def publish_event(event_type: str, payload: dict):
    url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange='messaging_events', exchange_type='topic', durable=True)
    ch.basic_publish(
        exchange='messaging_events',
        routing_key=event_type,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()
    print(f"[→] Published event: {event_type}")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def send_message(data: dict):
    sender_id    = int(data['senderID'])
    receiver_id  = int(data['receiverID'])
    content      = data['content']
    order_id     = data.get('orderID', 0)
    message_type = data.get('messageType', 'text')
    offer_amount = data.get('offerAmount', None)
    is_first     = data.get('isFirst', False)
    listing_name = data.get('listingName', '')
    listing_price = data.get('listingPrice', '')

    # ---------- Step 1: Store message ----------
    print(f"[1] Storing message from {sender_id} to {receiver_id}...")
    msg_payload = {
        "orderID":     order_id,
        "senderID":    sender_id,
        "receiverID":  receiver_id,
        "content":     content,
        "messageType": message_type,
    }
    if offer_amount is not None:
        msg_payload["offerAmount"] = offer_amount

    try:
        msg_resp = requests.post(
            f"{MESSAGING_URL}/messages",
            json=msg_payload,
            timeout=10
        )
        if msg_resp.status_code != 201:
            return {"error": "Failed to store message", "details": safe_json(msg_resp)}, 500
        message = msg_resp.json()
        print(f"[1] Message stored: {message.get('messageID')}")

        # Publish message event to RabbitMQ from negotiate composite.
        try:
            event_payload = {
                **message,
                "isFirst": is_first,
                "listingName": listing_name,
                "listingPrice": listing_price,
            }
            publish_event('message.sent', event_payload)
        except Exception as e:
            print(f"[1] WARNING: Could not publish message.sent: {e} — continuing anyway")
    except Exception as e:
        return {"error": f"Messaging service unreachable: {e}"}, 503

    return message, 201


def get_messages(order_id: int):
    print(f"[GET] Fetching messages for orderID={order_id}...")
    try:
        resp = requests.get(
            f"{MESSAGING_URL}/messages",
            params={"orderID": order_id},
            timeout=10
        )
        if resp.status_code != 200:
            return {"error": "Failed to fetch messages", "details": safe_json(resp)}, resp.status_code
        return resp.json(), 200
    except Exception as e:
        return {"error": f"Messaging service unreachable: {e}"}, 503
