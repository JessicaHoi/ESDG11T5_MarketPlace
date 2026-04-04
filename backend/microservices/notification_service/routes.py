from flask import Blueprint, request, jsonify, Response, stream_with_context
from models import db, Notification
from twilio_client import send_sms
import os
import json
import time
import queue
import threading

bp = Blueprint('notifications', __name__)

# ── SSE subscriber registry ───────────────────────────────────────────────────
_subscribers: dict[int, set] = {}
_lock = threading.Lock()


def _register(receiver_id: int) -> queue.Queue:
    q = queue.Queue(maxsize=50)
    with _lock:
        _subscribers.setdefault(receiver_id, set()).add(q)
    return q


def _unregister(receiver_id: int, q: queue.Queue):
    with _lock:
        subs = _subscribers.get(receiver_id, set())
        subs.discard(q)
        if not subs:
            _subscribers.pop(receiver_id, None)


def _push(receiver_id: int, data: dict):
    with _lock:
        queues = list(_subscribers.get(receiver_id, set()))
    print(f"[SSE] Pushing to receiverID={receiver_id} — {len(queues)} active connection(s)")
    for q in queues:
        try:
            q.put_nowait(data)
        except queue.Full:
            pass


# ── Phone number lookup ───────────────────────────────────────────────────────
def get_phone(user_id: int) -> str | None:
    phone_map = {
        1:  os.environ.get("BUYER_PHONE"),
        2:  os.environ.get("SELLER_PHONE"),
        99: os.environ.get("ADMIN_PHONE"),
    }
    return phone_map.get(user_id)


# ── GET /notification/stream?receiverID=X — SSE stream ───────────────────────
@bp.route('/notification/stream', methods=['GET'])
def stream_notifications():
    receiver_id = request.args.get('receiverID', type=int)
    if receiver_id is None:
        return jsonify({"error": "receiverID required"}), 400

    q = _register(receiver_id)

    def event_stream():
        yield f"event: connected\ndata: {json.dumps({'receiverID': receiver_id})}\n\n"
        print(f"[SSE] Connection opened for receiverID={receiver_id}")
        try:
            while True:
                try:
                    data = q.get(timeout=25)
                    yield f"event: notification\ndata: {json.dumps(data)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            _unregister(receiver_id, q)
            print(f"[SSE] Connection closed for receiverID={receiver_id}")

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':                'no-cache',
            'X-Accel-Buffering':            'no',
            'Connection':                   'keep-alive',
            'Access-Control-Allow-Origin':  '*',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )


# ── POST /notification — Save, push via SSE, send SMS ────────────────────────
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

    receiver_id = data['receiverID']

    # Push to SSE
    _push(receiver_id, note.to_dict())

    # Send SMS in a background thread so it doesn't get killed by Flask's threading model
    receiver_phone = data.get('receiverPhone') or get_phone(receiver_id)
    print(f"[SMS] Will attempt to send to receiverID={receiver_id}, phone={receiver_phone}")
    if receiver_phone:
        def _send():
            try:
                send_sms(to_number=receiver_phone, message=data['notification'])
                print(f"[✓] SMS sent to {receiver_phone}")
            except Exception as e:
                print(f"[!] SMS failed: {e}")
        threading.Thread(target=_send, daemon=True).start()

    return jsonify(note.to_dict()), 201


# ── POST /notification/<disputeID>/<notificationID> — Reminder ───────────────
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

    _push(original.receiverID, reminder.to_dict())

    data = request.get_json(silent=True) or {}
    receiver_phone = data.get('receiverPhone') or get_phone(original.receiverID)
    if receiver_phone:
        try:
            send_sms(to_number=receiver_phone, message=reminder_text)
        except Exception as e:
            print(f"[!] Reminder SMS failed: {e}")

    return jsonify(reminder.to_dict()), 201


# ── GET /notification/<notificationID> ───────────────────────────────────────
@bp.route('/notification/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    note = Notification.query.get_or_404(notification_id)
    return jsonify(note.to_dict())


# ── GET /notification?receiverID=X ───────────────────────────────────────────
@bp.route('/notification', methods=['GET'])
def get_notifications():
    receiver_id = request.args.get('receiverID', type=int)
    dispute_id  = request.args.get('disputeID',  type=int)

    query = Notification.query
    if receiver_id is not None:
        query = query.filter_by(receiverID=receiver_id)
    if dispute_id is not None:
        query = query.filter_by(disputeID=dispute_id)

    notes = query.order_by(Notification.sentAt.desc()).all()
    return jsonify([n.to_dict() for n in notes]), 200
