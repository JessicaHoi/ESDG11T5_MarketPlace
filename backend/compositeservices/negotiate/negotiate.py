import os, requests
from dotenv import load_dotenv

load_dotenv()

MESSAGING_URL    = os.environ.get("MESSAGING_SERVICE_URL", "http://messaging-service:5003")
NOTIFICATION_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5002")
SELLER_PHONE     = os.environ.get("SELLER_PHONE")
BUYER_PHONE      = os.environ.get("BUYER_PHONE")

PHONE_MAP = {
    1: BUYER_PHONE,
    2: SELLER_PHONE,
}


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
    except Exception as e:
        return {"error": f"Messaging service unreachable: {e}"}, 503

    # ---------- Step 2: Notify receiver ----------
    print(f"[2] Sending notification to {receiver_id}...")
    receiver_phone = PHONE_MAP.get(receiver_id) if is_first else None

    if is_first and listing_name:
        notif_text = (
            f"[Ouimarché] User #{sender_id} is interested in '{listing_name}' "
            f"(${listing_price}). They have started a negotiation chat."
        )
    else:
        preview = content[:60] + ('...' if len(content) > 60 else '')
        notif_text = f"[Ouimarché] New message: \"{preview}\""

    try:
        notif_payload = {
            "orderID":      order_id,
            "disputeID":    None,
            "notification": notif_text,
            "receiverID":   receiver_id,
        }
        if receiver_phone:
            notif_payload["receiverPhone"] = receiver_phone

        requests.post(
            f"{NOTIFICATION_URL}/notification",
            json=notif_payload,
            timeout=10
        )
        print(f"[2] Notification sent to {receiver_id}")
    except Exception as e:
        print(f"[2] WARNING: Notification failed: {e} — continuing anyway")

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


def get_deal(order_id: int):
    print(f"[GET] Fetching latest agreed deal for orderID={order_id}...")
    try:
        resp = requests.get(
            f"{MESSAGING_URL}/messages/deal",
            params={"orderID": order_id},
            timeout=10
        )
        if resp.status_code != 200:
            return {"error": "Failed to fetch latest deal", "details": safe_json(resp)}, resp.status_code
        return resp.json(), 200
    except Exception as e:
        return {"error": f"Messaging service unreachable: {e}"}, 503
