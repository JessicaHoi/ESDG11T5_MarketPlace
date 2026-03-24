from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

app = FastAPI(title="Order Service")


class OrderStatus(str, Enum):
    RESERVED = "RESERVED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"


class OrderCreate(BaseModel):
    buyer_id: int
    seller_id: int
    listing_id: int
    custom_me: Optional[str] = None
    order_details: Optional[str] = None
    agreed_price: float = Field(..., gt=0)


class OrderUpdate(BaseModel):
    custom_me: Optional[str] = None
    order_details: Optional[str] = None
    agreed_price: Optional[float] = Field(default=None, gt=0)
    status: Optional[OrderStatus] = None


class Order(BaseModel):
    order_id: int
    buyer_id: int
    seller_id: int
    listing_id: int
    custom_me: Optional[str] = None
    order_details: Optional[str] = None
    agreed_price: float
    status: OrderStatus
    created_at: datetime


orders_db: List[Order] = []
next_order_id = 1


@app.get("/")
def root():
    return {"message": "Order Service is running"}


@app.post("/orders", response_model=Order)
def create_order(order_data: OrderCreate):
    global next_order_id

    new_order = Order(
        order_id=next_order_id,
        buyer_id=order_data.buyer_id,
        seller_id=order_data.seller_id,
        listing_id=order_data.listing_id,
        custom_me=order_data.custom_me,
        order_details=order_data.order_details,
        agreed_price=order_data.agreed_price,
        status=OrderStatus.RESERVED,
        created_at=datetime.utcnow()
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

            if order_update.custom_me is not None:
                updated_data["custom_me"] = order_update.custom_me

            if order_update.order_details is not None:
                updated_data["order_details"] = order_update.order_details

            if order_update.agreed_price is not None:
                updated_data["agreed_price"] = order_update.agreed_price

            if order_update.status is not None:
                updated_data["status"] = order_update.status

            updated_order = Order(**updated_data)
            orders_db[index] = updated_order
            return updated_order

    raise HTTPException(status_code=404, detail="Order not found")


@app.put("/orders/{order_id}/confirm", response_model=Order)
def confirm_order(order_id: int):
    for index, order in enumerate(orders_db):
        if order.order_id == order_id:
            if order.status == OrderStatus.REFUNDED:
                raise HTTPException(
                    status_code=400,
                    detail="Refunded order cannot be confirmed"
                )

            updated_data = order.dict()
            updated_data["status"] = OrderStatus.COMPLETED

            updated_order = Order(**updated_data)
            orders_db[index] = updated_order
            return updated_order

    raise HTTPException(status_code=404, detail="Order not found")