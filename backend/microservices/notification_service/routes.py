from flask import Blueprint, request, jsonify, Response, stream_with_context
from models import db, Notification
from twilio_client import send_sms
import os
import json
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
    print(f"[SSE] Pushing to receiverID={receiver_id} — {len(queues)} active connection(s)", flush=True)
    for q in queues:
        try:
            q.put_nowait(data)
        except queue.Full:
            pass


# ── Phone number lookup ───────────────────────────────────────────────────────
def get_phone(user_id: int):
    phone_map = {
        1:  os.environ.get("BUYER_PHONE"),
        2:  os.environ.get("SELLER_PHONE"),
        99: os.environ.get("ADMIN_PHONE"),
    }
    return phone_map.get(user_id)


# ── Background worker: push SSE + send SMS ────────────────────────────────────
def _notify_async(receiver_id: int, message: str, receiver_phone: str, note_dict: dict):
    """Runs in a background thread — pushes SSE and sends SMS."""
    # Push to SSE
    _push(receiver_id, note_dict)

    # Send SMS
    print(f"[SMS] Attempting to {receiver_phone}: {message[:60]}", flush=True)
    try:
        send_sms(to_number=receiver_phone, message=message)
        print(f"[✓] SMS sent to {receiver_phone}", flush=True)
    except Exception as e:
        print(f"[!] SMS failed to {receiver_phone}: {e}", flush=True)


# ── GET /notification/stream?receiverID=X — SSE stream ───────────────────────
@bp.route('/notification/stream', methods=['GET'])
def stream_notifications():
    receiver_id = request.args.get('receiverID', type=int)
    if receiver_id is None:
        return jsonify({"error": "receiverID required"}), 400

    q = _register(receiver_id)

    def event_stream():
        yield f"event: connected\ndata: {json.dumps({'receiverID': receiver_id})}\n\n"
        print(f"[SSE] Connection opened for receiverID={receiver_id}", flush=True)
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
            print(f"[SSE] Connection closed for receiverID={receiver_id}", flush=True)

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


# ── POST /notification ────────────────────────────────────────────────────────
@bp.route('/notification', methods=['POST'])
def send_notification():
    data = request.get_json()

    # Save to DB first (fast, synchronous)
    note = Notification(
        orderID=data['orderID'],
        disputeID=data.get('disputeID'),
        notification=data['notification'],
        receiverID=data['receiverID'],
    )
    db.session.add(note)
    db.session.commit()

    receiver_id    = data['receiverID']
    message        = data['notification']
    receiver_phone = data.get('receiverPhone') or get_phone(receiver_id)
    note_dict      = note.to_dict()

    # Return immediately — do SSE push + SMS in background thread
    if receiver_phone:
        threading.Thread(
            target=_notify_async,
            args=(receiver_id, message, receiver_phone, note_dict),
            daemon=True
        ).start()
    else:
        # No phone — just push SSE (no SMS)
        threading.Thread(
            target=_push,
            args=(receiver_id, note_dict),
            daemon=True
        ).start()
        print(f"[!] No phone for receiverID={receiver_id} — SSE only", flush=True)

    return jsonify(note_dict), 201


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

    data           = request.get_json(silent=True) or {}
    receiver_phone = data.get('receiverPhone') or get_phone(original.receiverID)
    note_dict      = reminder.to_dict()

    if receiver_phone:
        threading.Thread(
            target=_notify_async,
            args=(original.receiverID, reminder_text, receiver_phone, note_dict),
            daemon=True
        ).start()
    else:
        threading.Thread(target=_push, args=(original.receiverID, note_dict), daemon=True).start()

    return jsonify(note_dict), 201


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
