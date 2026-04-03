from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os, time

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'mysql+mysqlconnector://root:root@localhost:3308/dispute'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class Dispute(db.Model):
    __tablename__ = 'dispute'

    disputeID      = db.Column(db.Integer, primary_key=True)
    orderID        = db.Column(db.Integer, nullable=True)
    buyerID        = db.Column(db.Integer, nullable=True)
    sellerID       = db.Column(db.Integer, nullable=True)
    disputeReason  = db.Column(db.String(500), nullable=False)
    disputeStatus  = db.Column(db.String(50), nullable=False)
    description    = db.Column(db.Text, nullable=True)
    amount         = db.Column(db.Numeric(10, 2), nullable=True)
    listingTitle   = db.Column(db.String(500), nullable=True)
    sellerResponse = db.Column(db.Text, nullable=True)
    deadlineAt     = db.Column(db.DateTime, nullable=True)
    createdAt      = db.Column(db.DateTime, nullable=True)

    def __init__(self, disputeID, disputeReason, disputeStatus,
                 deadlineAt=None, createdAt=None, orderID=None,
                 buyerID=None, sellerID=None, description=None,
                 amount=None, listingTitle=None, sellerResponse=None):
        self.disputeID      = disputeID
        self.orderID        = orderID
        self.buyerID        = buyerID
        self.sellerID       = sellerID
        self.disputeReason  = disputeReason
        self.disputeStatus  = disputeStatus
        self.description    = description
        self.amount         = amount
        self.listingTitle   = listingTitle
        self.sellerResponse = sellerResponse
        self.deadlineAt     = deadlineAt
        self.createdAt      = createdAt

    def json(self):
        return {
            "disputeID":      self.disputeID,
            "orderID":        self.orderID,
            "buyerID":        self.buyerID,
            "sellerID":       self.sellerID,
            "disputeReason":  self.disputeReason,
            "disputeStatus":  self.disputeStatus,
            "description":    self.description,
            "amount":         float(self.amount) if self.amount else None,
            "listingTitle":   self.listingTitle,
            "sellerResponse": self.sellerResponse,
            "deadlineAt":     self.deadlineAt.isoformat() if self.deadlineAt else None,
            "createdAt":      self.createdAt.isoformat() if self.createdAt else None,
        }


# ── GET all disputes (with optional filters) ─────────────────────────────────
@app.route("/dispute")
def get_all():
    query = Dispute.query

    order_id  = request.args.get('orderID',  type=int)
    buyer_id  = request.args.get('buyerID',  type=int)
    seller_id = request.args.get('sellerID', type=int)

    if order_id is not None:
        query = query.filter_by(orderID=order_id)
    if buyer_id is not None:
        query = query.filter_by(buyerID=buyer_id)
    if seller_id is not None:
        query = query.filter_by(sellerID=seller_id)

    dispute_list = query.all()
    if len(dispute_list):
        return jsonify({"code": 200, "data": {"disputes": [d.json() for d in dispute_list]}})
    return jsonify({"code": 404, "message": "There are no disputes."}), 404


# ── GET single dispute ────────────────────────────────────────────────────────
@app.route("/dispute/<int:disputeID>")
def find_by_disputeID(disputeID):
    dispute = db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID))
    if dispute:
        return jsonify({"code": 200, "data": dispute.json()})
    return jsonify({"code": 404, "message": "Dispute not found."}), 404


# ── CREATE dispute ────────────────────────────────────────────────────────────
@app.route("/dispute/<int:disputeID>", methods=['POST'])
def create_dispute(disputeID):
    if db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID)):
        return jsonify({"code": 400, "data": {"disputeID": disputeID},
                        "message": "Dispute already exists."}), 400
    data = request.get_json()
    dispute = Dispute(disputeID, **data)
    try:
        db.session.add(dispute)
        db.session.commit()
    except Exception as e:
        return jsonify({"code": 500, "data": {"disputeID": disputeID},
                        "message": str(e)}), 500
    return jsonify({"code": 201, "data": dispute.json()}), 201


# ── PATCH dispute (update fields) ────────────────────────────────────────────
@app.route("/dispute/<int:disputeID>", methods=['PATCH'])
def update_dispute(disputeID):
    dispute = db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID))
    if not dispute:
        return jsonify({"code": 404, "message": "Dispute not found."}), 404

    data = request.get_json()
    if 'disputeStatus' in data:
        dispute.disputeStatus = data['disputeStatus']
    if 'sellerResponse' in data:
        dispute.sellerResponse = data['sellerResponse']
    if 'deadlineAt' in data:
        dispute.deadlineAt = data['deadlineAt']
    if 'description' in data:
        dispute.description = data['description']
    if 'amount' in data:
        dispute.amount = data['amount']
    if 'listingTitle' in data:
        dispute.listingTitle = data['listingTitle']

    try:
        db.session.commit()
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500
    return jsonify({"code": 200, "data": dispute.json()})


# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=['GET'])
def health():
    return jsonify({"code": 200, "status": "dispute service running"}), 200


with app.app_context():
    retries = 5
    while retries:
        try:
            db.create_all()
            print("Dispute DB tables created.")
            break
        except Exception as e:
            retries -= 1
            print(f"DB not ready, retrying... ({e})")
            time.sleep(3)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
