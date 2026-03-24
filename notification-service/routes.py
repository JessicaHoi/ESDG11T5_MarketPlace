from flask import Blueprint, request, jsonify
from models import db, Notification
from twilio_client import send_sms

bp = Blueprint('notifications', __name__)

# POST /notification — Send notification manually
@bp.route('/notification', methods=['POST'])
def send_notification():
    data = request.get_json()
    note = Notification(
        orderID=data['orderID'],
        disputeID=data.get('disputeID'),
        notification=data['notification'],
        receiverID=data['receiverID'],
    )
    db.session.add(note)
    db.session.commit()
    return jsonify(note.to_dict()), 201

# POST /notification/<disputeID>/<notificationID> — Send reminder
@bp.route('/notification/<int:dispute_id>/<int:notification_id>', methods=['POST'])
def send_reminder(dispute_id, notification_id):
    original = Notification.query.get_or_404(notification_id)

    reminder_text = f"REMINDER: {original.notification}"

    reminder = Notification(
        orderID=original.orderID,
        disputeID=dispute_id,
        notification=reminder_text,
        receiverID=original.receiverID,
    )
    db.session.add(reminder)
    db.session.commit()

    # Send SMS if phone number provided in request body
    data = request.get_json(silent=True) or {}
    receiver_phone = data.get('receiverPhone')
    if receiver_phone:
        send_sms(
            to_number=receiver_phone,
            message=reminder_text
        )

    return jsonify(reminder.to_dict()), 201

# GET /notification/<notificationID> — Get a notification
@bp.route('/notification/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    note = Notification.query.get_or_404(notification_id)
    return jsonify(note.to_dict())