from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import stripe
import os

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "mysql+mysqlconnector://root@localhost:3308/payment_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_your_key_here")

db = SQLAlchemy(app)

class Payment(db.Model):
    __tablename__ = "payment"

    paymentID             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderID               = db.Column(db.Integer, nullable=False)
    amount                = db.Column(db.Numeric(10, 2), nullable=False)
    holdStatus            = db.Column(db.String(20), nullable=False, default="HELD")
    stripePaymentIntentID = db.Column(db.String(255), nullable=True)
    stripeStatus          = db.Column(db.String(50), nullable=True)
    createdAt             = db.Column(db.DateTime, default=datetime.now)
    updatedAt             = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def json(self):
        return {
            "paymentID":             self.paymentID,
            "orderID":               self.orderID,
            "amount":                float(self.amount),
            "holdStatus":            self.holdStatus,
            "stripePaymentIntentID": self.stripePaymentIntentID,
            "stripeStatus":          self.stripeStatus,
            "createdAt":             self.createdAt.isoformat(),
            "updatedAt":             self.updatedAt.isoformat(),
        }


# ── GET all payments (for testing/debugging) ──────────────────────────────────
@app.route("/payment", methods=["GET"])
def get_all_payments():
    payments = Payment.query.all()
    return jsonify({
        "code": 200,
        "data": [p.json() for p in payments]
    }), 200


# ── GET single payment by ID ──────────────────────────────────────────────────
@app.route("/payment/<int:paymentID>", methods=["GET"])
def get_payment(paymentID):
    payment = Payment.query.get(paymentID)
    if not payment:
        return jsonify({"code": 404, "message": "Payment not found"}), 404
    return jsonify({"code": 200, "data": payment.json()}), 200


# ── Hold payment in escrow ────────────────────────────────────────────────────
@app.route("/payment/escrow", methods=["POST"])
def hold_payment_in_escrow():
    data = request.get_json()

    required = ["orderID", "amount", "paymentMethodID"]
    for field in required:
        if field not in data:
            return jsonify({"code": 400, "message": f"Missing field: {field}"}), 400

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(data["amount"]) * 100),
            currency="sgd",
            payment_method=data["paymentMethodID"],
            capture_method="manual",
            confirm=True,
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never",
            },
            metadata={"orderID": str(data["orderID"])},
        )

        payment = Payment(
            orderID=data["orderID"],
            amount=data["amount"],
            holdStatus="HELD",
            stripePaymentIntentID=intent["id"],
            stripeStatus=intent["status"],
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            "code": 201,
            "message": "Payment held in escrow successfully.",
            "data": payment.json(),
        }), 201

    except stripe.error.StripeError as e:
        return jsonify({"code": 500, "message": f"Stripe error: {str(e)}"}), 500


# ── Release payment to seller ─────────────────────────────────────────────────
@app.route("/payment/release", methods=["POST"])
def release_payment():
    data = request.get_json()

    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    payment = Payment.query.filter_by(orderID=data["orderID"], holdStatus="HELD").first()
    if not payment:
        return jsonify({"code": 404, "message": "No held payment found for this order."}), 404

    try:
        intent = stripe.PaymentIntent.capture(payment.stripePaymentIntentID)
        payment.holdStatus   = "RELEASED"
        payment.stripeStatus = intent["status"]
        payment.updatedAt    = datetime.now()
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "Payment released to seller successfully.",
            "data": payment.json(),
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({"code": 500, "message": f"Stripe error: {str(e)}"}), 500


# ── Freeze payment during dispute ─────────────────────────────────────────────
@app.route("/payment/<int:paymentID>/freeze", methods=["PUT"])
@app.route("/payment/<int:paymentID>/freeze", methods=["PATCH"])
def freeze_payment(paymentID):
    payment = Payment.query.filter_by(paymentID=paymentID).first()
    if not payment:
        return jsonify({"code": 404, "message": "Payment not found."}), 404

    if payment.holdStatus != "HELD":
        return jsonify({
            "code": 400,
            "message": f"Cannot freeze payment with status: {payment.holdStatus}",
        }), 400

    payment.holdStatus = "FROZEN"
    payment.updatedAt  = datetime.now()
    db.session.commit()

    return jsonify({
        "code": 200,
        "message": "Payment frozen successfully.",
        "data": payment.json(),
    }), 200


# ── Refund buyer ──────────────────────────────────────────────────────────────
@app.route("/payment/refund", methods=["POST"])
def refund_payment():
    data = request.get_json()

    if "orderID" not in data:
        return jsonify({"code": 400, "message": "Missing field: orderID"}), 400

    payment = Payment.query.filter_by(orderID=data["orderID"], holdStatus="FROZEN").first()
    if not payment:
        return jsonify({"code": 404, "message": "No frozen payment found for this order."}), 404

    try:
        intent = stripe.PaymentIntent.cancel(payment.stripePaymentIntentID)
        payment.holdStatus   = "REFUNDED"
        payment.stripeStatus = intent["status"]
        payment.updatedAt    = datetime.now()
        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "Buyer refunded successfully.",
            "data": payment.json(),
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({"code": 500, "message": f"Stripe error: {str(e)}"}), 500


import time

with app.app_context():
    retries = 5
    while retries:
        try:
            db.create_all()
            print("Database tables created.")
            break
        except Exception as e:
            retries -= 1
            print(f"DB not ready, retrying... ({e})")
            time.sleep(3)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
