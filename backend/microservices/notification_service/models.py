from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Notification(db.Model):
    __tablename__ = 'notifications'

    notificationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    orderID        = db.Column(db.Integer, nullable=False)
    disputeID      = db.Column(db.Integer, nullable=True)
    notification   = db.Column(db.String(500))
    sentAt         = db.Column(db.DateTime, server_default=db.func.now())
    receiverID     = db.Column(db.Integer)

    def to_dict(self):
        return {
            "notificationID": self.notificationID,
            "orderID":        self.orderID,
            "disputeID":      self.disputeID,
            "notification":   self.notification,
            "sentAt":         str(self.sentAt),
            "receiverID":     self.receiverID,
        }