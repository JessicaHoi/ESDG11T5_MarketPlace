from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

DISPUTE_SERVICE_URL = os.environ.get('DISPUTE_SERVICE_URL', 'http://localhost:5000')
EVIDENCE_SERVICE_URL = os.environ.get('EVIDENCE_SERVICE_URL', 'http://localhost:5003')


def call_service(method, url, **kwargs):
    """Simple service caller"""
    try:
        resp = requests.request(method, url, timeout=10, **kwargs)
        return resp.json() if resp.text else {}, resp.status_code
    except requests.exceptions.ConnectionError:
        return {"code": 503, "message": f"Service unreachable: {url}"}, 503
    except Exception as e:
        return {"code": 500, "message": str(e)}, 500


@app.route("/report-problem", methods=['POST'])
def report_problem():
    """Create dispute and upload evidence"""
    data = request.get_json()
    
    required = ['orderID', 'buyerID', 'sellerID', 'reason', 'description']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"code": 400, "message": f"Missing fields: {missing}"}), 400
    
    dispute_body, dispute_code = call_service('POST', f"{DISPUTE_SERVICE_URL}/disputes", json={
        "orderID": data['orderID'],
        "buyerID": data['buyerID'],
        "sellerID": data['sellerID'],
        "reason": data['reason'],
        "description": data['description']
    })
    
    if dispute_code not in (200, 201):
        return jsonify({"code": dispute_code, "message": "Failed to create dispute"}), dispute_code
    
    dispute_id = dispute_body.get('data', {}).get('disputeID')
    
    evidence_results = []
    for item in data.get('evidence', []):
        ev_body, ev_code = call_service('POST', f"{EVIDENCE_SERVICE_URL}/evidence", json={
            "disputeID": dispute_id,
            "description": item.get('description', ''),
            "uploadedBy": data['buyerID'],
            "fileURL": item.get('fileURL', ''),
            "fileType": item.get('fileType', ''),
            "isApproved": False
        })
        evidence_results.append({"status": ev_code, "evidenceID": ev_body.get('data', {}).get('evidenceID')})
    
    return jsonify({
        "code": 201,
        "message": "Problem reported successfully",
        "data": {
            "disputeID": dispute_id,
            "orderID": data['orderID'],
            "evidenceUploaded": len([e for e in evidence_results if e['status'] in (200, 201)])
        }
    }), 201


@app.route("/report-problem/evidence/<int:evidence_id>/approve", methods=['PUT'])
def approve_evidence(evidence_id):
    """Approve evidence"""
    body, code = call_service('PUT', f"{EVIDENCE_SERVICE_URL}/evidence/{evidence_id}/approve")
    return jsonify(body), code


@app.route("/report-problem/dispute/<int:dispute_id>", methods=['PATCH'])
def update_dispute(dispute_id):
    """Update dispute status"""
    data = request.get_json()
    if not data or 'disputeStatus' not in data:
        return jsonify({"code": 400, "message": "Missing disputeStatus"}), 400
    
    body, code = call_service('PATCH', f"{DISPUTE_SERVICE_URL}/disputes/{dispute_id}", json=data)
    return jsonify(body), code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)