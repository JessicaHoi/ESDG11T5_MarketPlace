from flask import Blueprint, request, jsonify
from models import db, Message
from publisher import publish_event
from twilio_client import send_sms

bp = Blueprint('messaging', __name__)


# POST /messages — Send a message
@bp.route('/messages', methods=['POST'])
def send_message():
    data = request.get_json()

    message = Message(
        orderID=data['orderID'],
        senderID=data['senderID'],
        receiverID=data['receiverID'],
        content=data['content'],
        messageType=data.get('messageType', 'text'),
        offerAmount=data.get('offerAmount'),
    )
    db.session.add(message)
    db.session.commit()

    # Publish to RabbitMQ → Notification Service will pick this up
    publish_event('message.sent', message.to_dict())

    # Send SMS to receiver via Twilio (optional)
    receiver_phone = data.get('receiverPhone')
    if receiver_phone:
        send_sms(
            to_number=receiver_phone,
            message=f"New message from user {data['senderID']}: {data['content']}"
        )

    return jsonify(message.to_dict()), 201


# GET /messages/<messageID> — Get a single message by ID
@bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    message = Message.query.get_or_404(message_id)
    return jsonify(message.to_dict())


# GET /messages?orderID=X&senderID=Y&receiverID=Z — Get messages with optional filters
@bp.route('/messages', methods=['GET'])
def get_messages():
    order_id    = request.args.get('orderID',    type=int)
    sender_id   = request.args.get('senderID',   type=int)
    receiver_id = request.args.get('receiverID', type=int)

    query = Message.query

    if order_id is not None:
        query = query.filter_by(orderID=order_id)
    if sender_id is not None:
        query = query.filter_by(senderID=sender_id)
    if receiver_id is not None:
        query = query.filter_by(receiverID=receiver_id)

    messages = query.order_by(Message.sentAt.asc()).all()
    return jsonify([m.to_dict() for m in messages]), 200


# GET /messages/deal?orderID=X — Get latest agreed deal amount for a conversation
@bp.route('/messages/deal', methods=['GET'])
def get_latest_deal():
    order_id = request.args.get('orderID', type=int)
    if order_id is None:
        return jsonify({"error": "Missing required query param: orderID"}), 400

    agreement = (
        Message.query
        .filter_by(orderID=order_id, messageType='agreement')
        .order_by(Message.sentAt.desc(), Message.messageID.desc())
        .first()
    )

    if not agreement:
        return jsonify({"orderID": order_id, "deal": None}), 200

    return jsonify({
        "orderID": order_id,
        "deal": {
            "price": float(agreement.offerAmount) if agreement.offerAmount is not None else None,
            "messageID": agreement.messageID,
            "sentAt": str(agreement.sentAt),
            "senderID": agreement.senderID,
        }
    }), 200
