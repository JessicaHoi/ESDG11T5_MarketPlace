# ESDG11T5 MarketPlace

A second-hand marketplace platform built with a microservices architecture. Buyers can browse listings, place orders with escrow payment protection, and raise disputes. Sellers are notified at each step via RabbitMQ events.

---

## Architecture

### Composite Services
| Service | Port | Description |
|---|---|---|
| Place Order | 5006 | Orchestrates listing reservation → messaging → order creation → Stripe escrow payment → notification |
| Raise Dispute | 5010 | Orchestrates dispute creation → payment freeze → evidence upload → seller notification |

### Atomic Services
| Service | Port | Description |
|---|---|---|
| Order Service | 5001 | Manages order lifecycle (RESERVED → COMPLETED / DISPUTED / REFUNDED) |
| Payment Service | 5004 | Handles Stripe escrow payments (HELD → FROZEN / RELEASED / REFUNDED) |
| Listing Service | OutSystems | Manages item listings (external — OutSystems) |
| Messaging Service | 5007 | Stores buyer/seller messages, publishes to RabbitMQ |
| Notification Service | 5002 | Consumes RabbitMQ events and stores notifications |
| Dispute Service | 5005 | Manages dispute records and status |
| Evidence Service | 5003 | Stores dispute evidence files |

### Infrastructure
| Component | Port | Description |
|---|---|---|
| Kong API Gateway | 8000 | Routes all frontend API calls to the appropriate microservice |
| RabbitMQ | 5672 / 15672 | Message broker for async events (order.placed, dispute.raised, message.sent) |
| Frontend | 5173 | Vue 3 + Vite + Tailwind CSS buyer and admin interface |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Node.js 20+ (only needed if running the frontend outside Docker)

---

## Setup & Running

### 1. Start all services
```bash
docker compose up --build
```

This starts all microservices, databases, RabbitMQ, Kong, and the frontend in one command.

### 3. Access the app
| URL | Description |
|---|---|
| http://localhost:5173 | Main application |
| http://localhost:15672 | RabbitMQ management UI (guest / guest) |
| http://localhost:8000 | Kong API Gateway |

---

## Demo Credentials

On the login page, click the **demo credentials** button to auto-fill

---

## Key API Endpoints

All endpoints are accessible via Kong on port 8000, or directly on each service's port.

| Endpoint | Method | Description |
|---|---|---|
| `/placeorder` | POST | Place a new order (composite) |
| `/raise-dispute` | POST | Raise a dispute on an order (composite) |
| `/orders` | GET | Get all orders |
| `/orders/:id/confirm` | PUT | Confirm receipt → releases escrow |
| `/payment` | GET | Get all payment records |
| `/payment/escrow` | POST | Hold payment in escrow |
| `/dispute` | GET | Get all disputes |
| `/evidence` | POST | Upload dispute evidence |
| `/messages` | POST | Send a message |
| `/notification` | POST | Send a notification |

---

## User Flows

### Buyer — Place an Order
1. Browse listings → click a listing → **Buy Now**
2. Fill in contact details and click **Pay — Hold in Escrow**
3. Payment is held via Stripe. Order status: `RESERVED`
4. Once item is received, go to **My Orders** → **Confirm Receipt**
5. Escrow funds are released to seller. Order status: `COMPLETED`

### Buyer — Raise a Dispute
1. Go to **My Orders** → click **Raise Dispute** on a `RESERVED` order
2. Select a reason, describe the issue, optionally upload evidence
3. Click **Submit Dispute**
4. Payment is frozen. Seller has 48 hours to respond. Order status: `DISPUTED`

### Admin — Manage Disputes
1. Go to `http://localhost:5173/admin/disputes`
2. Review evidence and seller response
3. **Approve** → buyer is refunded | **Reject** → funds released to seller

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

- The **Listing Service** is hosted on OutSystems and is external to Docker Compose. Update `LISTING_SERVICE_URL` in `.env` once the URL is available. Steps 1 and 5 in `placeOrder.py` are currently commented out pending this.
- The **Order Service** uses in-memory storage — orders are reset on restart. This is intentional for the current demo phase.
- Stripe is running in **test mode** using `pm_card_visa` as the payment method for demo purposes.