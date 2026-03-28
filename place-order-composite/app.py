import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from placeorder import place_order

load_dotenv()

app = Flask(__name__)

@app.route('/placeorder', methods=['POST'])
def handle_place_order():
    data = request.get_json()

    # Validate required fields
    required = ['listingID', 'buyerID', 'sellerID', 'amount']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    result, status_code = place_order(data)
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)