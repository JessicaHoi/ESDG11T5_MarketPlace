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
    )
    db.session.add(message)
    db.session.commit()

    # Publish to RabbitMQ → Notification Service will pick this up
    publish_event('message.sent', message.to_dict())

    #send sms to receiver via twilio
    receiver_phone = data.get('receiverPhone')
    if receiver_phone:
        send_sms(
            to_number = receiver_phone,
            message = f"New message from user {data['senderID']}: {data['content']}"
        )

    return jsonify(message.to_dict()), 201


# GET /messages/<messageID> — Get a message/conversation
@bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    message = Message.query.get_or_404(message_id)
    return jsonify(message.to_dict())