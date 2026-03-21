from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)


DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3308')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'evidence')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3308/evidence'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Evidence(db.Model):
    __tablename__ = 'evidence'
    
    evidenceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    disputeID = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    uploadedBy = db.Column(db.Integer, nullable=False)
    fileURL = db.Column(db.String(500), nullable=False)
    fileType = db.Column(db.String(50), nullable=False)
    uploadedAt = db.Column(db.DateTime, default=datetime.utcnow)
    isApproved = db.Column(db.Boolean, default=False)
    
    def __init__(self, disputeID, description, uploadedBy, fileURL, fileType, isApproved=False):
        self.disputeID = disputeID
        self.description = description
        self.uploadedBy = uploadedBy
        self.fileURL = fileURL
        self.fileType = fileType
        self.isApproved = isApproved
    
    def json(self):
        return {
            "evidenceID": self.evidenceID,
            "disputeID": self.disputeID,
            "description": self.description,
            "uploadedBy": self.uploadedBy,
            "fileURL": self.fileURL,
            "fileType": self.fileType,
            "uploadedAt": self.uploadedAt.strftime("%Y-%m-%d %H:%M:%S") if self.uploadedAt else None,
            "isApproved": self.isApproved
        }


@app.route("/evidence/<int:disputeID>", methods=['GET'])
def get_evidence_by_dispute(disputeID):
    evidence_list = db.session.scalars(
        db.select(Evidence).filter_by(disputeID=disputeID)
    ).all()
    
    if evidence_list:
        return jsonify({
            "code": 200,
            "data": {
                "disputeID": disputeID,
                "evidence": [evidence.json() for evidence in evidence_list]
            }
        })
    return jsonify({
        "code": 404,
        "message": f"No evidence found for dispute ID: {disputeID}"
    }), 404


@app.route("/evidence/<int:disputeID>/<int:evidenceID>", methods=['GET'])
def get_evidence_by_id(disputeID, evidenceID):
    evidence = db.session.scalar(
        db.select(Evidence).filter_by(disputeID=disputeID, evidenceID=evidenceID)
    )
    
    if evidence:
        return jsonify({
            "code": 200,
            "data": evidence.json()
        })
    return jsonify({
        "code": 404,
        "message": f"Evidence with ID {evidenceID} not found for dispute ID: {disputeID}"
    }), 404


@app.route("/evidence", methods=['POST'])
def upload_evidence():
    try:
        data = request.get_json()
        
        
        required_fields = ['disputeID', 'description', 'uploadedBy', 'fileURL', 'fileType']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"Missing required field: {field}"
                }), 400
        

        evidence = Evidence(
            disputeID=data['disputeID'],
            description=data['description'],
            uploadedBy=data['uploadedBy'],
            fileURL=data['fileURL'],
            fileType=data['fileType'],
            isApproved=data.get('isApproved', False)
        )
        
        db.session.add(evidence)
        db.session.commit()
        
        return jsonify({
            "code": 201,
            "data": evidence.json(),
            "message": "Evidence uploaded successfully"
        }), 201
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route("/evidence/<int:evidenceID>/approve", methods=['PUT'])
def approve_evidence(evidenceID):
    try:
        evidence = db.session.scalar(
            db.select(Evidence).filter_by(evidenceID=evidenceID)
        )
        
        if not evidence:
            return jsonify({
                "code": 404,
                "message": f"Evidence with ID {evidenceID} not found"
            }), 404
        
        evidence.isApproved = True
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "data": evidence.json(),
            "message": "Evidence approved successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route("/evidence/all", methods=['GET'])
def get_all_evidence():
    evidence_list = db.session.scalars(db.select(Evidence)).all()
    
    if evidence_list:
        return jsonify({
            "code": 200,
            "data": {
                "evidence": [evidence.json() for evidence in evidence_list]
            }
        })
    return jsonify({
        "code": 404,
        "message": "No evidence found"
    }), 404


@app.route("/evidence/<int:evidenceID>", methods=['PUT'])
def update_evidence(evidenceID):
    try:
        evidence = db.session.scalar(
            db.select(Evidence).filter_by(evidenceID=evidenceID)
        )
        
        if not evidence:
            return jsonify({
                "code": 404,
                "message": f"Evidence with ID {evidenceID} not found"
            }), 404
        
        data = request.get_json()
        
       
        if 'description' in data:
            evidence.description = data['description']
        if 'fileURL' in data:
            evidence.fileURL = data['fileURL']
        if 'fileType' in data:
            evidence.fileType = data['fileType']
        
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "data": evidence.json(),
            "message": "Evidence updated successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"An error occurred: {str(e)}"
        }), 500


@app.route("/evidence/<int:evidenceID>", methods=['DELETE'])
def delete_evidence(evidenceID):
    try:
        evidence = db.session.scalar(
            db.select(Evidence).filter_by(evidenceID=evidenceID)
        )
        
        if not evidence:
            return jsonify({
                "code": 404,
                "message": f"Evidence with ID {evidenceID} not found"
            }), 404
        
        db.session.delete(evidence)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": f"Evidence with ID {evidenceID} deleted successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"An error occurred: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)