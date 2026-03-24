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