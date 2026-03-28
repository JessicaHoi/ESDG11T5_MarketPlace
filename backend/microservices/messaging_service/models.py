from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Message(db.Model):
    __tablename__ = 'messages'

    messageID  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderID    = db.Column(db.Integer, nullable=False)
    senderID   = db.Column(db.Integer, nullable=False)
    receiverID = db.Column(db.Integer, nullable=False)
    content    = db.Column(db.String(1000), nullable=False)
    sentAt     = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "messageID":  self.messageID,
            "orderID":    self.orderID,
            "senderID":   self.senderID,
            "receiverID": self.receiverID,
            "content":    self.content,
            "sentAt":     str(self.sentAt),
        }