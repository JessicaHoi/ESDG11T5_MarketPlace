import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from confirmStatus import confirm_delivery, confirm_receipt

load_dotenv()

app = Flask(__name__)
CORS(app)


# ── POST /confirm-status/delivered — Seller marks item as delivered ───────────
@app.route('/confirm-status/delivered', methods=['POST'])
def handle_confirm_delivery():
    data = request.get_json()
    required = ['orderID', 'sellerID', 'buyerID']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    result, status_code = confirm_delivery(data)
    return jsonify(result), status_code


# ── POST /confirm-status/receipt — Buyer confirms receipt ────────────────────
@app.route('/confirm-status/receipt', methods=['POST'])
def handle_confirm_receipt():
    data = request.get_json()
    required = ['orderID', 'buyerID', 'sellerID']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    result, status_code = confirm_receipt(data)
    return jsonify(result), status_code


# ── Health check ──────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"code": 200, "status": "confirmStatus composite service running"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)
