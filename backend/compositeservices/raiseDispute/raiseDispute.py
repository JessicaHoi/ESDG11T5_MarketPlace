from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pika
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)


DISPUTE_SERVICE_URL     = os.environ.get("DISPUTE_SERVICE_URL",     "http://dispute_service:5000")
PAYMENT_SERVICE_URL     = os.environ.get("PAYMENT_SERVICE_URL",     "http://payment_service:5000")
ORDER_SERVICE_URL       = os.environ.get("ORDER_SERVICE_URL",       "http://order_service:5000")
EVIDENCE_SERVICE_URL    = os.environ.get("EVIDENCE_SERVICE_URL",    "http://evidence_service:5003")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification_service:5000")
RABBITMQ_URL            = os.environ.get("RABBITMQ_URL",            "amqp://guest:guest@rabbitmq:5672/")



def publish_event(exchange: str, routing_key: str, payload: dict):
    """Fire-and-forget AMQP publish."""
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        conn   = pika.BlockingConnection(params)
        ch     = conn.channel()
        ch.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        ch.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),   # persistent
        )
        conn.close()
        print(f"[AMQP] Published {routing_key} → {exchange}")
    except Exception as exc:
        print(f"[AMQP] WARNING – could not publish event: {exc}")


@app.route("/raise-dispute", methods=["POST"])
def raise_dispute():
    data = request.get_json()

    required = ["orderID", "buyerID", "sellerID", "disputeReason",
                "paymentID", "fileURL", "fileType", "description"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"code": 400, "message": f"Missing fields: {missing}"}), 400

    order_id     = data["orderID"]
    buyer_id     = data["buyerID"]
    seller_id    = data["sellerID"]
    payment_id   = data["paymentID"]
    dispute_reason = data["disputeReason"]

    dispute_resp = requests.post(
        f"{DISPUTE_SERVICE_URL}/disputes",
        json={
            "orderID":       order_id,
            "buyerID":       buyer_id,
            "sellerID":      seller_id,
            "disputeReason": dispute_reason,
            "disputeStatus": "OPEN",
            "createdAt":     datetime.utcnow().isoformat(),
            "deadlineAt":    None,
        },
        timeout=10,
    )
    if dispute_resp.status_code not in (200, 201):
        return jsonify({
            "code":    dispute_resp.status_code,
            "step":    "create_dispute",
            "message": dispute_resp.json(),
        }), dispute_resp.status_code

    dispute_id = dispute_resp.json()["data"]["disputeID"]


    freeze_resp = requests.patch(
        f"{PAYMENT_SERVICE_URL}/payment/{payment_id}/freeze",
        timeout=10,
    )
    if freeze_resp.status_code != 200:
        return jsonify({
            "code":    freeze_resp.status_code,
            "step":    "freeze_payment",
            "message": freeze_resp.json(),
        }), freeze_resp.status_code

    order_resp = requests.get(
        f"{ORDER_SERVICE_URL}/orders/{order_id}",
        timeout=10,
    )
    if order_resp.status_code != 200:
        return jsonify({
            "code":    order_resp.status_code,
            "step":    "fetch_order",
            "message": order_resp.json(),
        }), order_resp.status_code

    order_details = order_resp.json()


    evidence_resp = requests.post(
        f"{EVIDENCE_SERVICE_URL}/evidence",
        json={
            "disputeID":   dispute_id,
            "description": data["description"],
            "uploadedBy":  buyer_id,
            "fileURL":     data["fileURL"],
            "fileType":    data["fileType"],
        },
        timeout=10,
    )
    if evidence_resp.status_code not in (200, 201):
        return jsonify({
            "code":    evidence_resp.status_code,
            "step":    "upload_evidence",
            "message": evidence_resp.json(),
        }), evidence_resp.status_code

    evidence_id = evidence_resp.json()["data"]["evidenceID"]

    publish_event(
        exchange    = "dispute_events",
        routing_key = "dispute.raised",
        payload     = {
            "orderID":       order_id,
            "disputeID":     dispute_id,
            "sellerID":      seller_id,
            "buyerID":       buyer_id,
            "disputeReason": dispute_reason,
        },
    )

    return jsonify({
        "code":    201,
        "message": "Dispute raised successfully. Seller notified.",
        "data": {
            "disputeID":   dispute_id,
            "evidenceID":  evidence_id,
            "paymentStatus": freeze_resp.json().get("data", {}).get("holdStatus"),
            "orderDetails":  order_details,
        },
    }), 201



@app.route("/raise-dispute/<int:dispute_id>/approve-evidence/<int:evidence_id>", methods=["PUT"])
def approve_evidence(dispute_id, evidence_id):

    approve_resp = requests.put(
        f"{EVIDENCE_SERVICE_URL}/evidence/{evidence_id}/approve",
        timeout=10,
    )
    if approve_resp.status_code != 200:
        return jsonify({
            "code":    approve_resp.status_code,
            "step":    "approve_evidence",
            "message": approve_resp.json(),
        }), approve_resp.status_code


    update_dispute_resp = requests.patch(
        f"{DISPUTE_SERVICE_URL}/disputes/{dispute_id}",
        json={"disputeStatus": "RESPONSE"},
        timeout=10,
    )
    if update_dispute_resp.status_code != 200:
        return jsonify({
            "code":    update_dispute_resp.status_code,
            "step":    "update_dispute",
            "message": update_dispute_resp.json(),
        }), update_dispute_resp.status_code

    return jsonify({
        "code":    200,
        "message": "Evidence approved and dispute updated to RESPONSE.",
        "data": {
            "evidence": approve_resp.json().get("data"),
            "dispute":  update_dispute_resp.json().get("data"),
        },
    }), 200


@app.route("/raise-dispute/<int:dispute_id>/resolve", methods=["POST"])
def resolve_dispute(dispute_id):
    data = request.get_json()
    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    order_id = data["orderID"]


    refund_resp = requests.post(
        f"{PAYMENT_SERVICE_URL}/payment/refund",
        json={"orderID": order_id},
        timeout=10,
    )
    if refund_resp.status_code != 200:
        return jsonify({
            "code":    refund_resp.status_code,
            "step":    "refund_payment",
            "message": refund_resp.json(),
        }), refund_resp.status_code

    update_dispute_resp = requests.patch(
        f"{DISPUTE_SERVICE_URL}/disputes/{dispute_id}",
        json={"disputeStatus": "RESOLVED"},
        timeout=10,
    )
    if update_dispute_resp.status_code != 200:
        return jsonify({
            "code":    update_dispute_resp.status_code,
            "step":    "update_dispute",
            "message": update_dispute_resp.json(),
        }), update_dispute_resp.status_code


    update_order_resp = requests.put(
        f"{ORDER_SERVICE_URL}/orders/{order_id}",
        json={"status": "REFUNDED"},
        timeout=10,
    )
    if update_order_resp.status_code != 200:
        return jsonify({
            "code":    update_order_resp.status_code,
            "step":    "update_order",
            "message": update_order_resp.json(),
        }), update_order_resp.status_code

    return jsonify({
        "code":    200,
        "message": "Dispute resolved. Buyer refunded. Order marked as REFUNDED.",
        "data": {
            "refund":  refund_resp.json().get("data"),
            "dispute": update_dispute_resp.json().get("data"),
            "order":   update_order_resp.json().get("data"),
        },
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"code": 200, "status": "raiseDispute composite service running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
