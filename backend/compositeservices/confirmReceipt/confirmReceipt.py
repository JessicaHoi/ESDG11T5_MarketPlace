import os
import requests
from dotenv import load_dotenv

load_dotenv()

ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service:8000")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://payment-service:5000")


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


def confirm_receipt(data: dict):
    order_id = data.get("orderID")
    if not order_id:
        return {"error": "Missing required field: orderID"}, 400

    # Step 1: Confirm order (DELIVERED -> COMPLETED)
    confirm_resp = requests.put(
        f"{ORDER_SERVICE_URL}/orders/{order_id}/confirm",
        timeout=10,
    )
    if confirm_resp.status_code != 200:
        return {
            "error": "Step 1 failed: Could not confirm order",
            "details": safe_json(confirm_resp),
        }, confirm_resp.status_code

    order_data = confirm_resp.json()

    # Step 2: Release held payment
    release_resp = requests.post(
        f"{PAYMENT_SERVICE_URL}/payment/release",
        json={"orderID": order_id},
        timeout=10,
    )
    if release_resp.status_code != 200:
        return {
            "message": "Order confirmed, but payment release failed.",
            "data": {
                "order": order_data,
                "payment": None,
                "releaseError": safe_json(release_resp),
            },
        }, 200

    return {
        "message": "Receipt confirmed and payment released successfully.",
        "data": {
            "order": order_data,
            "payment": safe_json(release_resp),
            "releaseError": None,
        },
    }, 200
