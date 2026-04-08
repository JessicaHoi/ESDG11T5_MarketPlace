from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Message(db.Model):
    __tablename__ = 'messages'

    messageID   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderID     = db.Column(db.Integer, nullable=False)
    senderID    = db.Column(db.Integer, nullable=False)
    receiverID  = db.Column(db.Integer, nullable=False)
    content     = db.Column(db.String(1000), nullable=False)
    messageType = db.Column(db.String(20), nullable=False, default='text')  # text | offer | agreement
    offerAmount = db.Column(db.Numeric(10, 2), nullable=True)
    sentAt      = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "messageID":   self.messageID,
            "orderID":     self.orderID,
            "senderID":    self.senderID,
            "receiverID":  self.receiverID,
            "content":     self.content,
            "messageType": self.messageType,
            "offerAmount": float(self.offerAmount) if self.offerAmount is not None else None,
            "sentAt":      str(self.sentAt),
        }