# Ouimarché — ESDG11T5 MarketPlace

A second-hand marketplace platform built with a microservices architecture. Buyers can browse listings, negotiate prices, place orders with escrow payment protection and raise disputes. All parties are notified at each step via SMS (Twilio), in-app bell notifications (SSE) and RabbitMQ events.

---

## Architecture

### Composite Services
| Service | Port | Description |
|---|---|---|
| Negotiate | 5008 | Orchestrates messaging between seller & buyer → notifications |
| Place Order | 5006 | Orchestrates order creation → Stripe escrow payment → seller notification |
| Confirm Status | 5009 | Orchestrates order status changes → payment release → notifications |
| Raise Dispute | 5010 | Orchestrates dispute creation → payment freeze → evidence upload → notifications |

### Atomic Services
| Service | Port | Description |
|---|---|---|
| Order Service | 5001 | Manages order lifecycle (RESERVED → DELIVERED → COMPLETED / DISPUTED / REFUNDED) |
| Payment Service | 5004 | Handles Stripe escrow payments (HELD → FROZEN / RELEASED / REFUNDED) |
| Listing Service | OutSystems | Manages item listings (external — OutSystems) |
| Messaging Service | 5007 | Stores buyer/seller messages, publishes to RabbitMQ |
| Notification Service | 5002 | Consumes RabbitMQ events, stores notifications, sends SMS via Twilio, pushes SSE |
| Dispute Service | 5005 | Manages dispute records and status |
| Evidence Service | 5003 | Stores dispute evidence files |

### Infrastructure
| Component | Port | Description |
|---|---|---|
| Kong API Gateway | 8000 | Routes all frontend API calls to the appropriate microservice |
| RabbitMQ | 5672 / 15672 | Message broker for async events (order.placed, order.confirmed, dispute.raised, etc.) |
| Frontend | 5173 | Vue 3 + Vite + Tailwind CSS — buyer, seller, and admin interfaces |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Node.js 20+ (only needed if running the frontend outside Docker)

---

## Setup & Running

### 1. Configure environment variables
Copy `.env.example` to `.env` and fill in your credentials:
```
STRIPE_SECRET_KEY=sk_test_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
BUYER_PHONE=+65...
SELLER_PHONE=+65...
ADMIN_PHONE=+65...
```

> **Note:** Twilio trial accounts can only send SMS to verified phone numbers. Add your number at [twilio.com/user/account/phone-numbers/verified](https://www.twilio.com/user/account/phone-numbers/verified).
>
> You must also update the matching phone numbers in `frontend/src/data/mockData.js` (`mockUser.phone` and `mockSeller.phone`) to match your verified Twilio number.

### 2. Start all services
```bash
docker compose up --build
```

This starts all microservices, databases, RabbitMQ, Kong, and the frontend in one command.

### 3. Access the app
| URL | Description |
|---|---|
| http://localhost:5173 | Main application |
| http://localhost:5173/seller | Seller portal |
| http://localhost:5173/admin | Admin portal |
| http://localhost:15672 | RabbitMQ management UI (guest / guest) |
| http://localhost:8000 | Kong API Gateway |

---

## Demo Credentials

On each login page, click the **demo credentials** button to auto-fill, or enter manually:

| Role | Email | Password |
|---|---|---|
| Buyer | mark@ouimarche.sg | password123 |
| Seller | ryan@ouimarche.sg | password123 |
| Admin | admin@ouimarche.sg | admin123 |

---

## Key API Endpoints

All endpoints are accessible via Kong on port 8000.

| Endpoint | Method | Description |
|---|---|---|
| `/placeorder` | POST | Place a new order (composite) |
| `/raise-dispute` | POST | Raise a dispute on an order (composite) |
| `/raise-dispute/:id/respond` | PATCH | Seller submits dispute response |
| `/raise-dispute/:id/seller-agree` | PATCH | Seller acknowledges dispute |
| `/raise-dispute/:id/resolve` | POST | Admin approves dispute → refunds buyer |
| `/raise-dispute/:id/reject` | POST | Admin rejects dispute → releases funds to seller |
| `/orders` | GET | Get all orders |
| `/orders/:id/deliver` | PUT | Seller marks order as delivered (RESERVED → DELIVERED) |
| `/orders/:id/confirm` | PUT | Buyer confirms receipt (DELIVERED → COMPLETED) |
| `/payment/escrow` | POST | Hold payment in escrow |
| `/payment/release` | POST | Release escrowed funds to seller |
| `/dispute` | GET | Get all disputes |
| `/evidence` | POST | Upload dispute evidence |
| `/messages` | POST | Send a message |
| `/notification` | POST | Send a notification (bell + SMS) |
| `/notification/stream` | GET | SSE stream for real-time bell notifications |

---

## User Flows

### Scenario 1 — Negotiate & Place an Order
1. Buyer browses listings → clicks a listing → **Negotiate**
2. Buyer sends first message → seller is notified via SMS + bell
3. Buyer and seller negotiate price via the messaging interface
4. Agreed price is stored on the frontend (localStorage)
5. Buyer clicks **Pay** → PlaceOrder composite:
   - Creates order in Order Service
   - Holds payment in escrow via Stripe
   - Notifies seller via SMS + bell
6. Order status: `RESERVED`

### Scenario 2 — Confirm Receipt
1. Seller goes to **My Orders** → clicks **Mark as Delivered**
   - Order status: `RESERVED → DELIVERED`
   - Buyer is notified via SMS + bell
2. Buyer sees **Confirm Receipt** button (only shown when `DELIVERED`)
3. Buyer clicks **Confirm Receipt**:
   - Order status: `DELIVERED → COMPLETED`
   - Escrow funds released to seller via Payment Service
   - Seller is notified via bell
4. Seller dashboard revenue updates automatically (sum of `agreed_price` for COMPLETED orders)

### Scenario 3 — Raise & Resolve a Dispute
1. Buyer goes to **My Orders** → **Raise Dispute** (available on `RESERVED` or `DELIVERED` orders)
2. Buyer selects a reason, describes the issue, uploads evidence → **Submit**
   - Payment frozen, Order status: `DISPUTED`
   - Seller and Admin notified via SMS + bell
3. Seller goes to **Disputes** → submits a response + optional evidence
   - 24-hour countdown timer resets
   - Buyer and Admin notified via bell
4. Seller clicks **Agreement Received**
   - Admin notified via SMS + bell
   - Buyer notified via bell
5. Admin reviews dispute → makes final decision:
   - **Approve** → buyer refunded, order status: `REFUNDED`
   - **Reject** → funds released to seller, order status: `COMPLETED`
   - Both parties notified via SMS + bell

---

## Stopping the App

```bash
# Stop containers (preserves all data)
docker compose down

# Stop and wipe all data (fresh start)
docker compose down -v
```

---

## Notes

- The **Listing Service** is hosted on OutSystems and is external to Docker Compose. Steps 1 and 5 in `placeOrder.py` (listing reservation / mark-as-sold) are currently commented out. Quantity changes are tracked locally via `localStorage` for demo purposes.
- The **Order Service** uses in-memory storage — orders reset on restart. This is intentional for the current demo phase.
- Stripe is running in **test mode** using `pm_card_visa` as the payment method.
- SSE (Server-Sent Events) for real-time bell notifications bypasses Kong directly to the Notification Service to avoid buffering issues.
- The negotiated price is NOT stored in the Listing Service — it is passed at payment time and stored as `agreed_price` on the Order record. This ensures other buyers always see the original listing price.
