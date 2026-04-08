from flask import Flask, request, jsonify
from dotenv import load_dotenv
from confirmReceipt import confirm_receipt

load_dotenv()

app = Flask(__name__)


@app.route('/confirm-receipt', methods=['POST'])
def handle_confirm_receipt():
    data = request.get_json() or {}
    result, status_code = confirm_receipt(data)
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=True)
