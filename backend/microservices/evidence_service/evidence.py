from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os, time

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqlconnector://{os.environ.get('DB_USER','root')}:"
    f"{os.environ.get('DB_PASSWORD','root')}@"
    f"{os.environ.get('DB_HOST','evidence-db')}:"
    f"{os.environ.get('DB_PORT','3308')}/"
    f"{os.environ.get('DB_NAME','evidence')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Evidence(db.Model):
    __tablename__ = 'evidence'

    evidenceID  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disputeID   = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    uploadedBy  = db.Column(db.Integer, nullable=False)
    fileURL     = db.Column(db.Text(length=16777215), nullable=True)       # base64 data URL or HTTP URL
    fileType    = db.Column(db.String(100), nullable=True)
    fileName    = db.Column(db.String(500), nullable=True)
    status      = db.Column(db.String(50), default='PENDING')
    createdAt   = db.Column(db.DateTime, default=datetime.utcnow)

    def json(self):
        return {
            "evidenceID":  self.evidenceID,
            "disputeID":   self.disputeID,
            "description": self.description,
            "uploadedBy":  self.uploadedBy,
            "fileURL":     self.fileURL,
            "fileType":    self.fileType,
            "fileName":    self.fileName,
            "status":      self.status,
            "createdAt":   self.createdAt.isoformat() if self.createdAt else None,
        }

# ── POST /evidence — Create evidence ─────────────────────────────────────────
@app.route('/evidence', methods=['POST'])
def create_evidence():
    data = request.get_json()
    evidence = Evidence(
        disputeID   = data['disputeID'],
        description = data.get('description'),
        uploadedBy  = data['uploadedBy'],
        fileURL     = data.get('fileURL'),
        fileType    = data.get('fileType'),
        fileName    = data.get('fileName'),
    )
    db.session.add(evidence)
    db.session.commit()
    return jsonify({"code": 201, "data": evidence.json()}), 201

# ── GET /evidence/<id> — Single evidence ──────────────────────────────────────
@app.route('/evidence/<int:evidence_id>', methods=['GET'])
def get_evidence(evidence_id):
    evidence = Evidence.query.get(evidence_id)
    if not evidence:
        return jsonify({"code": 404, "message": "Evidence not found"}), 404
    return jsonify({"code": 200, "data": evidence.json()}), 200

# ── GET /evidence?disputeID=X — All evidence for a dispute ───────────────────
@app.route('/evidence', methods=['GET'])
def get_evidence_by_dispute():
    dispute_id = request.args.get('disputeID', type=int)
    if dispute_id is None:
        all_evidence = Evidence.query.all()
        return jsonify({"code": 200, "data": [e.json() for e in all_evidence]}), 200

    evidence_list = Evidence.query.filter_by(disputeID=dispute_id).order_by(Evidence.createdAt.asc()).all()
    return jsonify({"code": 200, "data": [e.json() for e in evidence_list]}), 200

# ── PUT /evidence/<id>/approve ────────────────────────────────────────────────
@app.route('/evidence/<int:evidence_id>/approve', methods=['PUT'])
def approve_evidence(evidence_id):
    evidence = Evidence.query.get(evidence_id)
    if not evidence:
        return jsonify({"code": 404, "message": "Evidence not found"}), 404
    evidence.status = 'APPROVED'
    db.session.commit()
    return jsonify({"code": 200, "data": evidence.json()}), 200

# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"code": 200, "status": "evidence service running"}), 200

with app.app_context():
    retries = 5
    while retries:
        try:
            db.create_all()
            print("Evidence DB tables created.")
            break
        except Exception as e:
            retries -= 1
            print(f"DB not ready, retrying... ({e})")
            time.sleep(3)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)