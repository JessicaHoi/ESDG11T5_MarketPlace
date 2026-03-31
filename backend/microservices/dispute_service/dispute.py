from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'mysql+mysqlconnector://root:root@localhost:3308/dispute'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Dispute(db.Model):
    __tablename__ = 'dispute'

    disputeID = db.Column(db.Integer, primary_key=True)
    disputeReason = db.Column(db.String(500), nullable=False)
    disputeStatus = db.Column(db.String(50), nullable=False)
    deadlineAt = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime)

    def __init__(self, disputeID, disputeReason, disputeStatus, deadlineAt, createdAt):
        self.disputeID = disputeID
        self.disputeReason = disputeReason
        self.disputeStatus = disputeStatus
        self.deadlineAt = deadlineAt
        self.createdAt = createdAt

    def json(self):
        return {"disputeID": self.disputeID, "disputeReason": self.disputeReason, "disputeStatus": self.disputeStatus, "deadlineAt": self.deadlineAt, "createdAt": self.createdAt}

@app.route("/dispute")
def get_all():
    disputeList = db.session.scalars(db.select(Dispute)).all()
    if len(disputeList):
        return jsonify({"code": 200, "data": {"disputes": [dispute.json() for dispute in disputeList]}})
    return jsonify({"code": 404, "message": "There are no disputes."}), 404

@app.route("/dispute/<int:disputeID>")
def find_by_disputeID(disputeID):
    dispute = db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID))
    if dispute:
        return jsonify({"code": 200, "data": dispute.json()})
    return jsonify({"code": 404, "message": "Dispute not found."}), 404

@app.route("/dispute/<int:disputeID>", methods=['POST'])
def create_dispute(disputeID):
    if db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID)):
        return jsonify({"code": 400, "data": {"disputeID": disputeID}, "message": "Dispute already exists."}), 400
    data = request.get_json()
    dispute = Dispute(disputeID, **data)
    try:
        db.session.add(dispute)
        db.session.commit()
    except Exception as e:
        return jsonify({"code": 500, "data": {"disputeID": disputeID}, "message": str(e)}), 500
    return jsonify({"code": 201, "data": dispute.json()}), 201

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
