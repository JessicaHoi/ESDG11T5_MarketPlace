# Ouimarché — ESDG11T5 MarketPlace

A second-hand marketplace platform built on a microservices architecture. Buyers can browse listings, negotiate prices, place orders with escrow payment protection and raise disputes. All parties are notified at each step via SMS (Twilio), real-time in-app notifications (SSE) and AMQP events via RabbitMQ.

---

## Architecture

### Composite Services
| Service | Port | Description |
|---|---|---|
| Negotiate | 5008 | Orchestrates buyer-seller messaging → publishes `message.sent` via AMQP |
| Place Order | 5006 | Orchestrates order creation → Stripe escrow payment → publishes `order.placed` via AMQP |
| Confirm Status | 5009 | Orchestrates delivery confirmation and receipt confirmation → publishes `order.delivered` / `order.confirmed` via AMQP |
| Raise Dispute | 5010 | Orchestrates dispute creation → payment freeze → evidence upload → publishes dispute events via AMQP |

### Atomic Services
| Service | Port | Description |
|---|---|---|
| Order Service | 5001 | Manages order lifecycle (`RESERVED → DELIVERED → COMPLETED / DISPUTED / REFUNDED`) |
| Payment Service | 5004 | Handles Stripe escrow payments (`HELD → FROZEN / RELEASED / REFUNDED`) |
| Messaging Service | 5007 | Stores buyer/seller messages |
| Notification Service | 5002 | Consumes AMQP events → stores notifications → pushes SSE to browser → sends SMS via Twilio |
| Dispute Service | 5005 | Manages dispute records and status transitions |
| Evidence Service | 5003 | Stores dispute evidence files (base64 encoded) |
| Listing Service | OutSystems | External service — manages item listings (OutSystems cloud) |

### Infrastructure
| Component | Port | Description |
|---|---|---|
| Kong API Gateway | 8000 | Single entry point — routes all frontend API calls to the correct microservice |
| RabbitMQ | 5672 / 15672 | Message broker for async event-driven notifications |
| Frontend | 5173 | Vue 3 + Vite + Tailwind CSS — buyer, seller, and admin interfaces |

---

## Beyond-the-Labs (BTL) Features

### 1. Kong API Gateway
All frontend traffic routes through Kong on port 8000. Every microservice is registered as a Kong service with its own route path. Kong provides a single, unified entry point and decouples the frontend from individual service addresses.

### 2. Server-Sent Events (SSE) — Real-time Notifications
The Notification Service exposes a persistent SSE stream at `GET /notification/stream?receiverID=X`. The frontend subscribes to this on login and receives live push notifications whenever an AMQP event is consumed — no polling required. Each notification also triggers an SMS via Twilio if a phone number is available for the receiver.

---

## Event-Driven Architecture

All composite services communicate with the Notification Service exclusively via AMQP (RabbitMQ). The Notification Service is the sole consumer — it handles DB storage, SSE push, and SMS for every event.

| Exchange | Routing Key | Published by | Handler |
|---|---|---|---|
| `messaging_events` | `message.sent` | Negotiate | Notify message receiver |
| `order_events` | `order.placed` | Place Order | Notify buyer + seller |
| `order_events` | `order.delivered` | Confirm Status | Notify buyer to confirm receipt |
| `order_events` | `order.confirmed` | Confirm Status | Notify seller (payment released) + buyer |
| `dispute_events` | `dispute.raised` | Raise Dispute | Notify seller + buyer + admin |
| `dispute_events` | `dispute.seller_responded` | Raise Dispute | Notify buyer + admin |
| `dispute_events` | `dispute.seller_agreed` | Raise Dispute | Notify admin + buyer |
| `dispute_events` | `dispute.resolved` | Raise Dispute | Notify buyer + seller |
| `dispute_events` | `dispute.rejected` | Raise Dispute | Notify buyer + seller |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Node.js 20+ (only needed if running the frontend outside Docker)

---

## Setup & Running

### 1. Set up Twilio (for SMS notifications)

Twilio is used to send SMS notifications to buyers, sellers and admins at each step of every scenario.

**Step 1 — Create a free Twilio account**
1. Go to [twilio.com](https://www.twilio.com) and click **Sign up**
2. Verify your email address and complete the onboarding form
3. When asked what you want to build, select **SMS**

**Step 2 — Get your credentials**
1. Go to the [Twilio Console](https://console.twilio.com)
2. On the main dashboard you will see:
   - **Account SID** — copy this (starts with `AC...`)
   - **Auth Token** — click the eye icon to reveal, then copy it
3. Under **Phone Numbers → Manage → Active Numbers**, copy your free Twilio number (starts with `+1...`)

**Step 3 — Verify your personal phone number** (required for trial accounts)

Twilio trial accounts can only send SMS to verified numbers.
1. Go to [console.twilio.com/us1/develop/phone-numbers/manage/verified](https://console.twilio.com/us1/develop/phone-numbers/manage/verified)
2. Click **Add a new Caller ID**
3. Enter your mobile number (e.g. `+6591234567`) and verify via the OTP sent to your phone

> **For demo purposes:** Set `BUYER_PHONE`, `SELLER_PHONE`, and `ADMIN_PHONE` all to your own verified number so you receive all notifications on one device.

**Step 4 — Update phone numbers in two places**

> ⚠️ **Important:** The phone number must be updated in BOTH places below — missing either one means SMS will not fire correctly.

**Place 1 — `.env` file** (in the project root):
```env
BUYER_PHONE=+6591234567    # ← your verified mobile number
SELLER_PHONE=+6591234567   # ← same number for demo
ADMIN_PHONE=+6591234567    # ← same number for demo
```

**Place 2 — `frontend/src/data/mockData.js`** (two locations in this file):
```javascript
export const mockUser = {
  id: 1,
  name: 'Mark Foo',
  email: 'mark@ouimarche.sg',
  phone: '+6591234567',    // ← change this to your verified number
  ...
}

export const mockSeller = {
  id: 2,
  name: 'Ryan T.',
  email: 'ryan@ouimarche.sg',
  phone: '+6591234567',    // ← change this to your verified number
  ...
}
```

---

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
STRIPE_SECRET_KEY=sk_test_...

LISTING_SERVICE_URL=https://personal-8vnud50n.outsystemscloud.com/Listing/rest/Listing/listing/

TWILIO_ACCOUNT_SID=AC...          # from Twilio Console dashboard
TWILIO_AUTH_TOKEN=...             # from Twilio Console dashboard
TWILIO_PHONE_NUMBER=+1...         # your Twilio-provided number

BUYER_PHONE=+6591234567           # your verified mobile number
SELLER_PHONE=+6591234567          # your verified mobile number
ADMIN_PHONE=+6591234567           # your verified mobile number
```

### 3. Start all services

```bash
docker compose up --build
```

This starts all microservices, databases, RabbitMQ, Kong and the frontend in one command.

### 4. Access the app

| URL | Description |
|---|---|
| http://localhost:5173 | Buyer portal |
| http://localhost:5173/seller | Seller portal |
| http://localhost:5173/admin | Admin portal |
| http://localhost:8000 | Kong API Gateway |
| http://localhost:15672 | RabbitMQ management UI (guest / guest) |

### Backend service endpoints (for debugging)

| URL | Service |
|---|---|
| http://localhost:5001/orders | Order Service |
| http://localhost:5004/payment | Payment Service |
| http://localhost:5005/dispute | Dispute Service |
| http://localhost:5003/evidence | Evidence Service |
| http://localhost:5007/messages | Messaging Service |
| http://localhost:5002/notification | Notification Service |

---

## Demo Credentials

On each login page, click the **demo credentials** button to auto-fill, or enter manually:

| Role | Email | Password |
|---|---|---|
| Buyer | mark@ouimarche.sg | password123 |
| Seller | ryan@ouimarche.sg | password123 |
| Admin | admin@ouimarche.sg | admin123 |

---

## API Endpoints

All endpoints are accessible via Kong on port 8000 (`http://localhost:8000`).

### Composite — Negotiate
| Endpoint | Method | Description |
|---|---|---|
| `/negotiate/message` | POST | Send a message (stores + publishes AMQP event) |
| `/negotiate/messages` | GET | Get messages by `?orderID=X` |

### Composite — Place Order
| Endpoint | Method | Description |
|---|---|---|
| `/placeorder` | POST | Create order + hold Stripe escrow + publish `order.placed` |

### Composite — Confirm Status
| Endpoint | Method | Description |
|---|---|---|
| `/confirm-status/delivered` | POST | Seller marks order delivered + publish `order.delivered` |
| `/confirm-status/receipt` | POST | Buyer confirms receipt + release payment + publish `order.confirmed` |

### Composite — Raise Dispute
| Endpoint | Method | Description |
|---|---|---|
| `/raise-dispute` | POST | Raise dispute + freeze payment + upload evidence + publish `dispute.raised` |
| `/raise-dispute/:id/respond` | PATCH | Seller submits response + publish `dispute.seller_responded` |
| `/raise-dispute/:id/seller-agree` | PATCH | Seller agrees to refund + publish `dispute.seller_agreed` |
| `/raise-dispute/:id/approve-evidence/:eid` | PUT | Admin approves evidence |
| `/raise-dispute/:id/resolve` | POST | Admin approves → refund buyer + publish `dispute.resolved` |
| `/raise-dispute/:id/reject` | POST | Admin rejects → release to seller + publish `dispute.rejected` |
| `/raise-dispute/:id/message` | POST | Send dispute thread message |
| `/raise-dispute/:id/messages` | GET | Get dispute thread messages |

### Atomic — Orders
| Endpoint | Method | Description |
|---|---|---|
| `/orders` | GET | Get all orders (filter by `?buyerID=` or `?sellerID=`) |
| `/orders/:id` | GET | Get single order |
| `/orders/:id` | PATCH | Partial update order (status, price, details) |
| `/orders/:id/confirm` | PUT | Confirm order → status `COMPLETED` |

### Atomic — Payment
| Endpoint | Method | Description |
|---|---|---|
| `/payment` | GET | Get all payments |
| `/payment/escrow` | POST | Hold payment in escrow via Stripe |
| `/payment/release` | POST | Release escrowed funds to seller |
| `/payment/refund` | POST | Refund buyer via Stripe |
| `/payment/:id/freeze` | PATCH | Freeze payment during dispute |

### Atomic — Notifications
| Endpoint | Method | Description |
|---|---|---|
| `/notification` | GET | Get notifications (filter by `?receiverID=` or `?disputeID=`) |
| `/notification/:id` | GET | Get single notification |
| `/notification` | POST | Create notification → SSE push + SMS |
| `/notification/stream` | GET | SSE stream for real-time push (`?receiverID=X`) |
| `/notification/:disputeID/:notifID` | POST | Send reminder notification |

### Atomic — Messaging
| Endpoint | Method | Description |
|---|---|---|
| `/messages` | GET | Get messages (filter by `?orderID=`, `?senderID=`, `?receiverID=`) |
| `/messages/:id` | GET | Get single message |
| `/messages` | POST | Store a message |

### Atomic — Dispute
| Endpoint | Method | Description |
|---|---|---|
| `/dispute` | GET | Get disputes (filter by `?buyerID=`, `?sellerID=`, `?orderID=`) |
| `/dispute/:id` | GET | Get single dispute |
| `/dispute/:id` | PATCH | Partial update dispute (status, response, deadline) |

### Atomic — Evidence
| Endpoint | Method | Description |
|---|---|---|
| `/evidence` | GET | Get evidence (filter by `?disputeID=`) |
| `/evidence/:id` | GET | Get single evidence |
| `/evidence` | POST | Upload evidence file |
| `/evidence/:id/approve` | PUT | Approve evidence |

---

## User Flows

### Scenario 1 — Negotiate & Place an Order

**Negotiation phase:**
1. Buyer browses listings → clicks a listing → opens negotiation chat
2. Buyer sends first message → Negotiate composite stores message → publishes `message.sent` via AMQP → seller notified via SMS + SSE
3. Buyer and seller negotiate price via the messaging interface
4. Agreed price saved in browser `localStorage` via `saveDeal()`

**Purchase phase:**
5. Buyer clicks **Pay $X** → PlaceOrder composite:
   - Creates order in Order Service (`PATCH /orders`)
   - Holds payment in escrow via Stripe (`POST /payment/escrow`)
   - Decrements listing stock in OutSystems (GET + PUT — best-effort)
   - Publishes `order.placed` via AMQP → buyer + seller notified via SSE + SMS
6. Order status: `RESERVED`

---

### Scenario 2 — Confirm Delivery & Receipt

**Step 1 — Seller marks as delivered:**
1. Seller goes to **My Orders** → clicks **Mark as Delivered**
2. ConfirmStatus composite:
   - Updates order to `DELIVERED` (`PATCH /orders/:id`)
   - Publishes `order.delivered` via AMQP → buyer notified via SSE + SMS

**Step 2 — Buyer confirms receipt:**
3. Buyer sees **Confirm Receipt** button (shown only for `DELIVERED` orders)
4. ConfirmStatus composite:
   - Confirms order → status `COMPLETED` (`PUT /orders/:id/confirm`)
   - Releases escrowed funds to seller via Stripe (`POST /payment/release`)
   - Publishes `order.confirmed` via AMQP → seller + buyer notified via SSE + SMS

---

### Scenario 3 — Raise & Resolve a Dispute

1. Buyer goes to **My Orders** → **Raise Dispute** (available on `RESERVED` or `DELIVERED` orders)
2. Buyer selects reason, describes issue, uploads evidence → **Submit**
   - RaiseDispute composite: creates dispute → freezes payment → uploads evidence → updates order to `DISPUTED`
   - Publishes `dispute.raised` → seller + buyer + admin notified via SSE + SMS
3. Seller goes to **Disputes** → submits response + optional evidence
   - Publishes `dispute.seller_responded` → buyer + admin notified via SSE + SMS
   - 24-hour response deadline resets
4. Seller clicks **Agreement Received**
   - Dispute status → `AWAITING_DECISION`
   - Publishes `dispute.seller_agreed` → admin + buyer notified via SSE + SMS
5. Admin reviews dispute → final decision:
   - **Approve** → buyer refunded via Stripe, order → `REFUNDED`, publishes `dispute.resolved`
   - **Reject** → funds released to seller, order → `COMPLETED`, publishes `dispute.rejected`
   - Both parties notified via SSE + SMS

---

## Stopping the App

```bash
# Stop containers (preserves all DB data)
docker compose down

# Stop and wipe all data (fresh start)
docker compose down -v
```

---

## Notes

- The **Listing Service** is hosted externally on OutSystems. Stock quantity is decremented via GET + PUT to OutSystems on purchase.
- The **Order Service** uses in-memory storage — orders reset on container restart. Intentional for the current demo phase.
- The **Messaging Service** is a pure atomic service — it stores messages only. All AMQP publishing is handled by the Negotiate composite service.
- **Stripe** runs in test mode using `pm_card_visa` as the payment method.
- **SSE stream** (`/notification/stream`) connects directly to the Notification Service, bypassing Kong, to prevent response buffering from breaking the persistent connection.
- The **negotiated price** is not stored in the Listing Service — it is passed at payment time and stored as `agreed_price` on the Order record so other buyers always see the original listing price.
- All **HTTP method conventions**: POST = create, GET = read, PUT = full update, PATCH = partial update. Notably, order status changes use PATCH (partial), while order confirmation uses PUT (defined endpoint).