<<<<<<< Updated upstream
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

app = FastAPI(title="Dispute Service")


class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    NEGOTIATING = "NEGOTIATING"
    RESOLVED_BUYER = "RESOLVED_BUYER"
    RESOLVED_SELLER = "RESOLVED_SELLER"
    AUTO_REFUNDED = "AUTO_REFUNDED"
    CLOSED = "CLOSED"


class SenderRole(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    SYSTEM = "SYSTEM"


class DisputeCreate(BaseModel):
    order_id: int
    buyer_id: int
    seller_id: int
    reason: str = Field(..., min_length=3)
    evidence: Optional[str] = None


class NegotiationMessageCreate(BaseModel):
    sender_role: SenderRole
    sender_id: int
    message: str = Field(..., min_length=1)


class DisputeResolve(BaseModel):
    outcome: DisputeStatus


class NegotiationMessage(BaseModel):
    message_id: int
    dispute_id: int
    sender_role: SenderRole
    sender_id: int
    message: str
    created_at: datetime


class Dispute(BaseModel):
    dispute_id: int
    order_id: int
    buyer_id: int
    seller_id: int
    reason: str
    evidence: Optional[str] = None
    status: DisputeStatus
    created_at: datetime
    seller_response_deadline: datetime
    resolved_at: Optional[datetime] = None


disputes_db: List[Dispute] = []
messages_db: List[NegotiationMessage] = []
next_dispute_id = 1
next_message_id = 1


@app.get("/")
def root():
    return {"message": "Dispute Service is running"}


@app.post("/disputes", response_model=Dispute)
def raise_dispute(dispute_data: DisputeCreate):
    global next_dispute_id

    new_dispute = Dispute(
        dispute_id=next_dispute_id,
        order_id=dispute_data.order_id,
        buyer_id=dispute_data.buyer_id,
        seller_id=dispute_data.seller_id,
        reason=dispute_data.reason,
        evidence=dispute_data.evidence,
        status=DisputeStatus.OPEN,
        created_at=datetime.utcnow(),
        seller_response_deadline=datetime.utcnow() + timedelta(hours=48),
        resolved_at=None
    )

    disputes_db.append(new_dispute)
    next_dispute_id += 1
    return new_dispute


@app.get("/disputes", response_model=List[Dispute])
def get_all_disputes():
    return disputes_db


@app.get("/disputes/{dispute_id}", response_model=Dispute)
def get_dispute(dispute_id: int):
    for dispute in disputes_db:
        if dispute.dispute_id == dispute_id:
            return dispute
    raise HTTPException(status_code=404, detail="Dispute not found")


@app.post("/disputes/{dispute_id}/messages", response_model=NegotiationMessage)
def add_negotiation_message(dispute_id: int, msg_data: NegotiationMessageCreate):
    global next_message_id

    dispute_index = None
    for index, dispute in enumerate(disputes_db):
        if dispute.dispute_id == dispute_id:
            dispute_index = index
            break

    if dispute_index is None:
        raise HTTPException(status_code=404, detail="Dispute not found")

    dispute = disputes_db[dispute_index]

    if dispute.status in {
        DisputeStatus.RESOLVED_BUYER,
        DisputeStatus.RESOLVED_SELLER,
        DisputeStatus.AUTO_REFUNDED,
        DisputeStatus.CLOSED,
    }:
        raise HTTPException(status_code=400, detail="Dispute is already closed")

    new_message = NegotiationMessage(
        message_id=next_message_id,
        dispute_id=dispute_id,
        sender_role=msg_data.sender_role,
        sender_id=msg_data.sender_id,
        message=msg_data.message,
        created_at=datetime.utcnow()
    )

    messages_db.append(new_message)
    next_message_id += 1

    updated_dispute = dispute.model_copy(update={"status": DisputeStatus.NEGOTIATING})
    disputes_db[dispute_index] = updated_dispute

    return new_message


@app.get("/disputes/{dispute_id}/messages", response_model=List[NegotiationMessage])
def get_dispute_messages(dispute_id: int):
    dispute_exists = any(d.dispute_id == dispute_id for d in disputes_db)
    if not dispute_exists:
        raise HTTPException(status_code=404, detail="Dispute not found")

    return [msg for msg in messages_db if msg.dispute_id == dispute_id]


@app.put("/disputes/{dispute_id}/resolve", response_model=Dispute)
def resolve_dispute(dispute_id: int, resolution: DisputeResolve):
    for index, dispute in enumerate(disputes_db):
        if dispute.dispute_id == dispute_id:
            if resolution.outcome not in {
                DisputeStatus.RESOLVED_BUYER,
                DisputeStatus.RESOLVED_SELLER,
                DisputeStatus.CLOSED,
            }:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid resolution outcome"
                )

            updated_dispute = dispute.model_copy(
                update={
                    "status": resolution.outcome,
                    "resolved_at": datetime.utcnow()
                }
            )
            disputes_db[index] = updated_dispute
            return updated_dispute

    raise HTTPException(status_code=404, detail="Dispute not found")


@app.put("/disputes/{dispute_id}/auto-refund", response_model=Dispute)
def auto_refund_dispute(dispute_id: int):
    for index, dispute in enumerate(disputes_db):
        if dispute.dispute_id == dispute_id:
            if datetime.utcnow() < dispute.seller_response_deadline:
                raise HTTPException(
                    status_code=400,
                    detail="Seller response deadline has not passed yet"
                )

            updated_dispute = dispute.model_copy(
                update={
                    "status": DisputeStatus.AUTO_REFUNDED,
                    "resolved_at": datetime.utcnow()
                }
            )
            disputes_db[index] = updated_dispute
            return updated_dispute

    raise HTTPException(status_code=404, detail="Dispute not found")
=======
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pika
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DISPUTE_SERVICE_URL      = os.environ.get("DISPUTE_SERVICE_URL",      "http://dispute-service:5000")
PAYMENT_SERVICE_URL      = os.environ.get("PAYMENT_SERVICE_URL",      "http://payment-service:5000")
ORDER_SERVICE_URL        = os.environ.get("ORDER_SERVICE_URL",        "http://order-service:8000")
EVIDENCE_SERVICE_URL     = os.environ.get("EVIDENCE_SERVICE_URL",     "http://evidence-service:5003")
RABBITMQ_URL             = os.environ.get("RABBITMQ_URL",             "amqp://guest:guest@rabbitmq:5672/")


def publish_event(exchange: str, routing_key: str, payload: dict):
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


@app.route("/raise-dispute", methods=["POST"])
def raise_dispute():
    data = request.get_json()
    print(f"[raise-dispute] Received: {json.dumps(data)}")

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

    # ---------- Step 1: Create dispute ----------
    # Use a timestamp-based ID to avoid collisions
    import time
    dispute_id = int(time.time())
    dispute_resp = requests.post(
        f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}",
        json={
            "disputeReason": dispute_reason,
            "disputeStatus": "OPEN",
            "createdAt":     datetime.utcnow().isoformat(),
            "deadlineAt":    None,
        },
        timeout=10,
    )
    if dispute_resp.status_code not in (200, 201):
        print(f"[raise-dispute] Step 1 failed: {dispute_resp.status_code} {dispute_resp.text}")
        return jsonify({
            "code":    dispute_resp.status_code,
            "step":    "create_dispute",
            "message": dispute_resp.text,
        }), dispute_resp.status_code

    # ---------- Step 2: Freeze payment (best-effort) ----------
    freeze_status = "NOT_FROZEN"
    if payment_id and payment_id != 0:
        freeze_resp = requests.put(
            f"{PAYMENT_SERVICE_URL}/payment/{payment_id}/freeze",
            timeout=10,
        )
        if freeze_resp.status_code == 200:
            freeze_status = freeze_resp.json().get("data", {}).get("holdStatus", "FROZEN")
            print(f"[raise-dispute] Step 2: Payment {payment_id} frozen")
        else:
            print(f"[raise-dispute] Step 2 WARNING: Could not freeze payment {payment_id}: {freeze_resp.text}")
    else:
        print(f"[raise-dispute] Step 2 SKIPPED: No valid paymentID provided ({payment_id})")

    # ---------- Step 3: Fetch order details ----------
    order_details = {}
    try:
        order_resp = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}", timeout=10)
        if order_resp.status_code == 200:
            order_details = order_resp.json()
    except Exception as e:
        print(f"[raise-dispute] Step 3 WARNING: Could not fetch order: {e}")

    # ---------- Step 4: Upload evidence ----------
    evidence_id = None
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
        print(f"[raise-dispute] Step 4 WARNING: Could not upload evidence: {evidence_resp.text}")
    else:
        evidence_id = evidence_resp.json().get("data", {}).get("evidenceID")

    # ---------- Step 5: Publish AMQP event ----------
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

    # ---------- Step 6: Update order status to DISPUTED ----------
    try:
        requests.put(
            f"{ORDER_SERVICE_URL}/orders/{order_id}",
            json={"status": "DISPUTED"},
            timeout=10,
        )
        print(f"[raise-dispute] Step 6: Order {order_id} marked DISPUTED")
    except Exception as e:
        print(f"[raise-dispute] Step 6 WARNING: Could not update order status: {e}")

    return jsonify({
        "code":    201,
        "message": "Dispute raised successfully. Seller notified.",
        "data": {
            "disputeID":     dispute_id,
            "evidenceID":    evidence_id,
            "paymentStatus": freeze_status,
            "orderDetails":  order_details,
        },
    }), 201


@app.route("/raise-dispute/<int:dispute_id>/approve-evidence/<int:evidence_id>", methods=["PUT"])
def approve_evidence(dispute_id, evidence_id):
    approve_resp = requests.put(f"{EVIDENCE_SERVICE_URL}/evidence/{evidence_id}/approve", timeout=10)
    if approve_resp.status_code != 200:
        return jsonify({"code": approve_resp.status_code, "step": "approve_evidence", "message": approve_resp.text}), approve_resp.status_code

    update_dispute_resp = requests.patch(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}", json={"disputeStatus": "RESPONSE"}, timeout=10)

    return jsonify({
        "code":    200,
        "message": "Evidence approved and dispute updated to RESPONSE.",
        "data": {
            "evidence": approve_resp.json().get("data"),
            "dispute":  update_dispute_resp.json().get("data") if update_dispute_resp.status_code == 200 else None,
        },
    }), 200


@app.route("/raise-dispute/<int:dispute_id>/resolve", methods=["POST"])
def resolve_dispute(dispute_id):
    data = request.get_json()
    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    order_id = data["orderID"]

    refund_resp = requests.post(f"{PAYMENT_SERVICE_URL}/payment/refund", json={"orderID": order_id}, timeout=10)
    if refund_resp.status_code != 200:
        return jsonify({"code": refund_resp.status_code, "step": "refund_payment", "message": refund_resp.text}), refund_resp.status_code

    requests.patch(f"{DISPUTE_SERVICE_URL}/dispute/{dispute_id}", json={"disputeStatus": "RESOLVED"}, timeout=10)
    requests.put(f"{ORDER_SERVICE_URL}/orders/{order_id}", json={"status": "REFUNDED"}, timeout=10)

    return jsonify({"code": 200, "message": "Dispute resolved. Buyer refunded.", "data": {"refund": refund_resp.json().get("data")}}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"code": 200, "status": "raiseDispute composite service running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
>>>>>>> Stashed changes
