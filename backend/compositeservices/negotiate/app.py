import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from negotiate import send_message, get_messages

load_dotenv()

app = Flask(__name__)
CORS(app)


@app.route('/negotiate/message', methods=['POST'])
def handle_send_message():
    data = request.get_json()
    required = ['senderID', 'receiverID', 'content']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    result, status_code = send_message(data)
    return jsonify(result), status_code


@app.route('/negotiate/messages', methods=['GET'])
def handle_get_messages():
    order_id = request.args.get('orderID', type=int)
    if order_id is None:
        return jsonify({"error": "Missing required query param: orderID"}), 400
    result, status_code = get_messages(order_id)
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
