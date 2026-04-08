from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pika
import json
import os
import time
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DISPUTE_SERVICE_URL      = os.environ.get("DISPUTE_SERVICE_URL",      "http://dispute-service:5000")
PAYMENT_SERVICE_URL      = os.environ.get("PAYMENT_SERVICE_URL",      "http://payment-service:5000")
ORDER_SERVICE_URL        = os.environ.get("ORDER_SERVICE_URL",        "http://order-service:8000")
EVIDENCE_SERVICE_URL     = os.environ.get("EVIDENCE_SERVICE_URL",     "http://evidence-service:5003")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://notification-service:5002")
MESSAGING_SERVICE_URL    = os.environ.get("MESSAGING_SERVICE_URL",    "http://messaging-service:5003")
RABBITMQ_URL             = os.environ.get("RABBITMQ_URL",             "amqp://guest:guest@rabbitmq:5672/")


def publish_event(exchange: str, routing_key: str, payload: dict):
    """Publish an event to RabbitMQ — notification service consumes and handles all notifications."""
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        conn   = pika.BlockingConnection(params)
        ch     = conn.channel()
        ch.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        ch.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        conn.close()
        print(f"[AMQP] Published {routing_key} → {exchange}")
    except Exception as exc:
        print(f"[AMQP] WARNING – could not publish event: {exc}")


# ── POST /raise-dispute — Buyer raises a new dispute ────────────────────────
@app.route("/raise-dispute", methods=["POST"])
def raise_dispute():
    data = request.get_json()
    log_data = {k: v for k, v in data.items() if k not in ('files', 'fileURL')}
    print(f"[raise-dispute] Received: {json.dumps(log_data)} (files omitted from log)")

    required = ["orderID", "buyerID", "sellerID", "disputeReason",
                "paymentID", "fileURL", "fileType", "description"]
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"code": 400, "message": f"Missing fields: {missing}"}), 400

    order_id       = data["orderID"]
    buyer_id       = data["buyerID"]
    seller_id      = data["sellerID"]
    payment_id     = data["paymentID"]
    dispute_reason = data["disputeReason"]
    listing_title  = data.get("listingTitle", f"Order #{order_id}")
    amount         = data.get("amount", 0)

    now      = datetime.utcnow()
    deadline = now + timedelta(hours=24)

    # ---------- Step 1: Create dispute ----------
    dispute_id   = int(time.time())
    dispute_resp = requests.post(
        f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
        json={
            "disputeReason": dispute_reason,
            "disputeStatus": "OPEN",
            "description":   data["description"],
            "orderID":       order_id,
            "buyerID":       buyer_id,
            "sellerID":      seller_id,
            "amount":        amount,
            "listingTitle":  listing_title,
            "createdAt":     now.isoformat(),
            "deadlineAt":    deadline.isoformat(),
        },
        timeout=10,
    )
    if dispute_resp.status_code not in (200, 201):
        return jsonify({
            "code":    dispute_resp.status_code,
            "step":    "create_dispute",
            "message": dispute_resp.text,
        }), dispute_resp.status_code

    # ---------- Step 2: Freeze payment (best-effort) ----------
    freeze_status = "NOT_FROZEN"
    if payment_id and payment_id != 0:
        freeze_resp = requests.patch(
            f"{PAYMENT_SERVICE_URL}/payment/{payment_id}/freeze", timeout=10)
        if freeze_resp.status_code == 200:
            freeze_status = freeze_resp.json().get("data", {}).get("holdStatus", "FROZEN")
            print(f"[raise-dispute] Step 2: Payment {payment_id} frozen")
        else:
            print(f"[raise-dispute] Step 2 WARNING: Could not freeze payment: {freeze_resp.text}")
    else:
        print(f"[raise-dispute] Step 2 SKIPPED: No valid paymentID ({payment_id})")

    # ---------- Step 3: Fetch order details ----------
    order_details = {}
    try:
        order_resp = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}", timeout=10)
        if order_resp.status_code == 200:
            order_details = order_resp.json()
    except Exception as e:
        print(f"[raise-dispute] Step 3 WARNING: Could not fetch order: {e}")

    # ---------- Step 4: Upload buyer evidence ----------
    evidence_id = None
    files_data  = data.get("files", [])
    if not files_data:
        files_data = [{
            "fileURL":  data["fileURL"],
            "fileType": data["fileType"],
            "fileName": data.get("fileName", "evidence-file"),
        }]

    for file_entry in files_data:
        evidence_resp = requests.post(
            f"{EVIDENCE_SERVICE_URL}/evidence",
            json={
                "disputeID":   dispute_id,
                "description": data["description"],
                "uploadedBy":  buyer_id,
                "fileURL":     file_entry.get("fileURL", ""),
                "fileType":    file_entry.get("fileType", ""),
                "fileName":    file_entry.get("fileName", ""),
            },
            timeout=10,
        )
        if evidence_resp.status_code not in (200, 201):
            print(f"[raise-dispute] Step 4 WARNING: Could not upload evidence: {evidence_resp.text}")
        else:
            if evidence_id is None:
                evidence_id = evidence_resp.json().get("data", {}).get("evidenceID")

    # ---------- Step 5: Update order status to DISPUTED ----------
    try:
        requests.patch(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            json={"status": "DISPUTED"},
            timeout=10,
        )
        print(f"[raise-dispute] Step 5: Order {order_id} marked DISPUTED")
    except Exception as e:
        print(f"[raise-dispute] Step 5 WARNING: Could not update order status: {e}")

    # ---------- Step 6: Publish AMQP event → notification service handles SMS + SSE ----------
    publish_event(
        exchange    = "dispute_events",
        routing_key = "dispute.raised",
        payload     = {
            "orderID":       order_id,
            "disputeID":     dispute_id,
            "sellerID":      seller_id,
            "buyerID":       buyer_id,
            "disputeReason": dispute_reason,
            "listingTitle":  listing_title,
            "amount":        amount,
        },
    )

    return jsonify({
        "code":    201,
        "message": "Dispute raised successfully. Seller notified via AMQP.",
        "data": {
            "disputeID":     dispute_id,
            "evidenceID":    evidence_id,
            "paymentStatus": freeze_status,
            "orderDetails":  order_details,
            "deadlineAt":    deadline.isoformat(),
        },
    }), 201


# ── PATCH /raise-dispute/<id>/respond — Seller submits response ──────────────
@app.route("/raise-dispute/<int:dispute_id>/respond", methods=["PATCH"])
def seller_respond(dispute_id):
    data          = request.get_json()
    response_text = data.get("sellerResponse", "")
    if not response_text:
        return jsonify({"code": 400, "message": "sellerResponse is required"}), 400

    new_deadline = datetime.utcnow() + timedelta(hours=24)

    # Update dispute with seller response and reset deadline
    update_resp = requests.patch(
        f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
        json={
            "sellerResponse": response_text,
            "disputeStatus":  "RESPONSE",
            "deadlineAt":     new_deadline.isoformat(),
        },
        timeout=10,
    )
    if update_resp.status_code != 200:
        return jsonify({"code": update_resp.status_code, "step": "update_dispute",
                        "message": update_resp.text}), update_resp.status_code

    dispute_data = update_resp.json().get("data", {})
    order_id     = dispute_data.get("orderID", 0)
    buyer_id     = dispute_data.get("buyerID", 0)
    seller_id    = dispute_data.get("sellerID", 0)

    # Upload seller evidence files (best-effort)
    for file_entry in data.get('files', []):
        try:
            requests.post(
                f"{EVIDENCE_SERVICE_URL}/evidence",
                json={
                    "disputeID":   dispute_id,
                    "description": f"Seller evidence for dispute #{dispute_id}",
                    "uploadedBy":  seller_id,
                    "fileURL":     file_entry.get('fileURL', ''),
                    "fileType":    file_entry.get('fileType', ''),
                    "fileName":    file_entry.get('fileName', ''),
                },
                timeout=10
            )
        except Exception as e:
            print(f"[seller-respond] WARNING: Could not upload evidence: {e}")

    # Publish AMQP event → notification service notifies buyer + admin
    publish_event("dispute_events", "dispute.seller_responded", {
        "disputeID":    dispute_id,
        "orderID":      order_id,
        "buyerID":      buyer_id,
        "sellerID":     seller_id,
        "listingTitle": dispute_data.get("listingTitle", ""),
        "amount":       dispute_data.get("amount", 0),
    })

    return jsonify({
        "code":    200,
        "message": "Seller response recorded. Timer reset. Buyer notified via AMQP.",
        "data":    dispute_data,
    }), 200


# ── PATCH /raise-dispute/<id>/seller-agree — Seller agrees to refund ─────────
@app.route("/raise-dispute/<int:dispute_id>/seller-agree", methods=["PATCH"])
def seller_agree(dispute_id):
    update_resp = requests.patch(
        f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
        json={"disputeStatus": "AWAITING_DECISION"},
        timeout=10,
    )
    if update_resp.status_code != 200:
        return jsonify({"code": update_resp.status_code, "step": "update_dispute",
                        "message": update_resp.text}), update_resp.status_code

    dispute_data = update_resp.json().get("data", {})
    order_id     = dispute_data.get("orderID", 0)
    buyer_id     = dispute_data.get("buyerID", 0)
    seller_id    = dispute_data.get("sellerID", 0)

    # Publish AMQP event → notification service notifies admin + buyer
    publish_event("dispute_events", "dispute.seller_agreed", {
        "disputeID":    dispute_id,
        "orderID":      order_id,
        "buyerID":      buyer_id,
        "sellerID":     seller_id,
        "amount":       dispute_data.get("amount", 0),
        "listingTitle": dispute_data.get("listingTitle", ""),
    })

    return jsonify({
        "code":    200,
        "message": "Agreement received. Admin notified via AMQP.",
        "data":    dispute_data,
    }), 200


# ── PUT /raise-dispute/<id>/approve-evidence/<eid> — Admin approves evidence ──
@app.route("/raise-dispute/<int:dispute_id>/approve-evidence/<int:evidence_id>", methods=["PUT"])
def approve_evidence(dispute_id, evidence_id):
    approve_resp = requests.put(
        f"{EVIDENCE_SERVICE_URL}/evidence/{evidence_id}/approve", timeout=10)
    if approve_resp.status_code != 200:
        return jsonify({"code": approve_resp.status_code, "step": "approve_evidence",
                        "message": approve_resp.text}), approve_resp.status_code

    update_dispute_resp = requests.patch(
        f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
        json={"disputeStatus": "RESPONSE"},
        timeout=10,
    )

    return jsonify({
        "code":    200,
        "message": "Evidence approved and dispute updated to RESPONSE.",
        "data": {
            "evidence": approve_resp.json().get("data"),
            "dispute":  update_dispute_resp.json().get("data") if update_dispute_resp.status_code == 200 else None,
        },
    }), 200


# ── POST /raise-dispute/<id>/resolve — Admin approves → refund buyer ─────────
@app.route("/raise-dispute/<int:dispute_id>/resolve", methods=["POST"])
def resolve_dispute(dispute_id):
    data = request.get_json()
    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    order_id = data["orderID"]

    # Refund buyer via payment service
    refund_resp = requests.post(
        f"{PAYMENT_SERVICE_URL}/payment/refund",
        json={"orderID": order_id}, timeout=10)
    if refund_resp.status_code != 200:
        print(f"[resolve] WARNING: Refund failed: {refund_resp.text}")

    # Update dispute status to APPROVED
    requests.patch(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
                   json={"disputeStatus": "APPROVED"}, timeout=10)

    # Update order status to REFUNDED
    requests.patch(f"{ORDER_SERVICE_URL}/orders/{order_id}",
                 json={"status": "REFUNDED"}, timeout=10)

    # Fetch dispute for notification payload
    dispute_data = {}
    try:
        dr = requests.get(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}", timeout=10)
        if dr.status_code == 200:
            dispute_data = dr.json().get("data", {})
    except:
        pass

    buyer_id  = dispute_data.get("buyerID",  data.get("buyerID",  0))
    seller_id = dispute_data.get("sellerID", data.get("sellerID", 0))
    amount    = dispute_data.get("amount",   0)
    listing   = dispute_data.get("listingTitle", "")

    # Publish AMQP event → notification service notifies buyer + seller
    publish_event("dispute_events", "dispute.resolved", {
        "disputeID":    dispute_id,
        "orderID":      order_id,
        "outcome":      "APPROVED",
        "buyerID":      buyer_id,
        "sellerID":     seller_id,
        "amount":       amount,
        "listingTitle": listing,
    })

    return jsonify({
        "code":    200,
        "message": "Dispute approved. Buyer refunded. Notifications sent via AMQP.",
        "data": {"refund": refund_resp.json() if refund_resp.status_code == 200 else None},
    }), 200


# ── POST /raise-dispute/<id>/reject — Admin rejects → release to seller ───────
@app.route("/raise-dispute/<int:dispute_id>/reject", methods=["POST"])
def reject_dispute(dispute_id):
    data = request.get_json()
    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    order_id = data["orderID"]

    # Release payment to seller
    release_resp = requests.post(
        f"{PAYMENT_SERVICE_URL}/payment/release",
        json={"orderID": order_id}, timeout=10)
    if release_resp.status_code != 200:
        print(f"[reject] WARNING: Release failed: {release_resp.text}")

    # Update dispute status to REJECTED
    requests.patch(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
                   json={"disputeStatus": "REJECTED"}, timeout=10)

    # Update order status to COMPLETED
    requests.patch(f"{ORDER_SERVICE_URL}/orders/{order_id}",
                 json={"status": "COMPLETED"}, timeout=10)

    # Fetch dispute for notification payload
    dispute_data = {}
    try:
        dr = requests.get(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}", timeout=10)
        if dr.status_code == 200:
            dispute_data = dr.json().get("data", {})
    except:
        pass

    buyer_id  = dispute_data.get("buyerID",  data.get("buyerID",  0))
    seller_id = dispute_data.get("sellerID", data.get("sellerID", 0))
    amount    = dispute_data.get("amount",   0)
    listing   = dispute_data.get("listingTitle", "")

    # Publish AMQP event → notification service notifies buyer + seller
    publish_event("dispute_events", "dispute.rejected", {
        "disputeID":    dispute_id,
        "orderID":      order_id,
        "outcome":      "REJECTED",
        "buyerID":      buyer_id,
        "sellerID":     seller_id,
        "amount":       amount,
        "listingTitle": listing,
    })

    return jsonify({
        "code":    200,
        "message": "Dispute rejected. Payment released to seller. Notifications sent via AMQP.",
        "data": {"release": release_resp.json() if release_resp.status_code == 200 else None},
    }), 200


# ── POST /raise-dispute/<id>/message — Send dispute thread message ────────────
@app.route("/raise-dispute/<int:dispute_id>/message", methods=["POST"])
def send_dispute_message(dispute_id):
    data        = request.get_json()
    sender_id   = data.get('senderID')
    receiver_id = data.get('receiverID')
    content     = data.get('content', '')
    if not content or not sender_id or not receiver_id:
        return jsonify({"code": 400, "message": "senderID, receiverID and content are required"}), 400

    try:
        msg_resp = requests.post(
            f"{MESSAGING_SERVICE_URL}/messages",
            json={
                "orderID":     -dispute_id,
                "senderID":    sender_id,
                "receiverID":  receiver_id,
                "content":     content,
                "messageType": "text",
            },
            timeout=10
        )
        if msg_resp.status_code not in (200, 201):
            return jsonify({"code": msg_resp.status_code, "message": msg_resp.text}), msg_resp.status_code

        # Notify receiver via direct HTTP (in-app only, no SMS for thread messages)
        try:
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notification",
                json={
                    "orderID":      0,
                    "disputeID":    dispute_id,
                    "notification": f"[Ouimarché] New message in Dispute #{dispute_id}: \"{content[:60]}{'...' if len(content) > 60 else ''}\"",
                    "receiverID":   receiver_id,
                },
                timeout=10
            )
        except Exception as e:
            print(f"[dispute-message] WARNING: Notification failed: {e}")

        return jsonify(msg_resp.json()), 201
    except Exception as e:
        return jsonify({"code": 503, "message": str(e)}), 503


# ── GET /raise-dispute/<id>/messages — Fetch dispute thread messages ──────────
@app.route("/raise-dispute/<int:dispute_id>/messages", methods=["GET"])
def get_dispute_messages(dispute_id):
    try:
        resp = requests.get(
            f"{MESSAGING_SERVICE_URL}/messages",
            params={"orderID": -dispute_id},
            timeout=10
        )
        if resp.status_code != 200:
            return jsonify({"code": resp.status_code, "message": resp.text}), resp.status_code
        return jsonify(resp.json()), 200
    except Exception as e:
        return jsonify({"code": 503, "message": str(e)}), 503


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"code": 200, "status": "raiseDispute composite service running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
