from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

app = FastAPI(title="Order Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderStatus(str, Enum):
    RESERVED  = "RESERVED"
    COMPLETED = "COMPLETED"
    REFUNDED  = "REFUNDED"
    DISPUTED  = "DISPUTED"


# ── Input models ──────────────────────────────────────────────────────────────
# Accepts both camelCase (from placeOrder composite) and snake_case

class OrderCreate(BaseModel):
    # snake_case (direct calls)
    buyer_id:      Optional[int]   = None
    seller_id:     Optional[int]   = None
    listing_id:    Optional[int]   = None
    agreed_price:  Optional[float] = None
    order_details: Optional[str]   = None
    custom_me:     Optional[str]   = None

    # camelCase (from placeOrder composite)
    buyerID:   Optional[int]   = None
    sellerID:  Optional[int]   = None
    listingID: Optional[int]   = None
    amount:    Optional[float] = None
    status:    Optional[str]   = None  # ignored on create, always RESERVED

    def resolved_buyer_id(self)   -> int:   return self.buyer_id   or self.buyerID   or 0
    def resolved_seller_id(self)  -> int:   return self.seller_id  or self.sellerID  or 0
    def resolved_listing_id(self) -> int:   return self.listing_id or self.listingID or 0
    def resolved_price(self)      -> float: return self.agreed_price or self.amount  or 0.0


class OrderUpdate(BaseModel):
    custom_me:     Optional[str]         = None
    order_details: Optional[str]         = None
    agreed_price:  Optional[float]       = Field(default=None, gt=0)
    status:        Optional[OrderStatus] = None


# ── Output model ──────────────────────────────────────────────────────────────

class Order(BaseModel):
    order_id:      int
    buyer_id:      int
    seller_id:     int
    listing_id:    int
    custom_me:     Optional[str]  = None
    order_details: Optional[str]  = None
    agreed_price:  float
    status:        OrderStatus
    created_at:    datetime


# ── Seed data ─────────────────────────────────────────────────────────────────
# Gives the frontend something to display while the Listing (OutSystems)
# service is not yet available. Replace / remove once the real service is live.

orders_db: List[Order] = [
    Order(
        order_id=1,
        buyer_id=1,
        seller_id=2,
        listing_id=3,
        order_details="Nintendo Switch OLED (White)",
        agreed_price=330.0,
        status=OrderStatus.RESERVED,
        created_at=datetime(2026, 3, 20, 10, 0, 0),
    ),
    Order(
        order_id=2,
        buyer_id=1,
        seller_id=3,
        listing_id=6,
        order_details="MacBook Air M2 13\" 256GB",
        agreed_price=1100.0,
        status=OrderStatus.COMPLETED,
        created_at=datetime(2026, 3, 15, 14, 30, 0),
    ),
    Order(
        order_id=3,
        buyer_id=1,
        seller_id=4,
        listing_id=1,
        order_details="Sony WH-1000XM5 Headphones",
        agreed_price=220.0,
        status=OrderStatus.DISPUTED,
        created_at=datetime(2026, 3, 10, 9, 0, 0),
    ),
]

next_order_id = len(orders_db) + 1


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Order Service is running"}


@app.post("/orders", response_model=Order, status_code=201)
def create_order(order_data: OrderCreate):
    global next_order_id

    new_order = Order(
        order_id=next_order_id,
        buyer_id=order_data.resolved_buyer_id(),
        seller_id=order_data.resolved_seller_id(),
        listing_id=order_data.resolved_listing_id(),
        custom_me=order_data.custom_me,
        order_details=order_data.order_details,
        agreed_price=order_data.resolved_price(),
        status=OrderStatus.RESERVED,
        created_at=datetime.utcnow(),
    )

    orders_db.append(new_order)
    next_order_id += 1
    return new_order


@app.get("/orders", response_model=List[Order])
def get_all_orders():
    return orders_db


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    for order in orders_db:
        if order.order_id == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")


@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: int, order_update: OrderUpdate):
    for index, order in enumerate(orders_db):
        if order.order_id == order_id:
            updated_data = order.dict()
            if order_update.custom_me     is not None: updated_data["custom_me"]     = order_update.custom_me
            if order_update.order_details is not None: updated_data["order_details"] = order_update.order_details
            if order_update.agreed_price  is not None: updated_data["agreed_price"]  = order_update.agreed_price
            if order_update.status        is not None: updated_data["status"]        = order_update.status
            updated_order = Order(**updated_data)
            orders_db[index] = updated_order
            return updated_order
    raise HTTPException(status_code=404, detail="Order not found")


@app.put("/orders/{order_id}/confirm", response_model=Order)
def confirm_order(order_id: int):
    for index, order in enumerate(orders_db):
        if order.order_id == order_id:
            if order.status == OrderStatus.REFUNDED:
                raise HTTPException(status_code=400, detail="Refunded order cannot be confirmed")
            updated_data = order.dict()
            updated_data["status"] = OrderStatus.COMPLETED
            updated_order = Order(**updated_data)
            orders_db[index] = updated_order
            return updated_order
    raise HTTPException(status_code=404, detail="Order not found")
