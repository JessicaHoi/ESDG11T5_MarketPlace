from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3308/dispute'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

class Dispute(db.Model):
    __tablename__ = 'dispute'

    disputeID = db.Column(db.Integer, primary_key=True)
    disputeReason = db.Column(db.String, nullable=False)
    disputeStatus = db.Column(db.String, nullable=False)
    deadlineAt = db.Column(db.DateTime)
    createdAt = db.Column(db.DateTime)

    def __init__(self, disputeID, disputeReason, disputeStatus, deadlineAt, createdAt):
        self.disputeID = disputeID
        self.disputeReason = disputeReason
        self.disputeStatus = disputeStatus
        self.deadlineAt = deadlineAt
        self.createdAt = createdAt

    def json(self):
        return {"disputeID": self.disputeID, "disputeReason": self.disputeReason, "disputeStatus": self.disputeStatus, "deadlineAt": self.deadlineAt, "createdAt": self.createdAt}

@app.route("/dispute")

def get_all():
    disputeList = db.session.scalars(db.select(Dispute)).all()


    if len(disputeList):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "disputes": [dispute.json() for dispute in disputeList]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no disputes."
        }
    ), 404

@app.route("/dispute/<int:disputeID>")
def find_by_disputeID(disputeID):
    dispute = db.session.scalar(
    	db.select(Dispute).filter_by(disputeID=disputeID)
)


    if dispute:
        return jsonify(
            {
                "code": 200,
                "data": dispute.json()
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "Book not found."
        }
    ), 404



@app.route("/dispute/<int:disputeID>", methods=['POST'])
def create_dispute(disputeID):
    if db.session.scalar(db.select(Dispute).filter_by(disputeID=disputeID)):
        return jsonify(
            {
                "code": 400,
                "data": {
                    "disputeID": disputeID
                },
                "message": "Dispute already exists."
            }
        ), 400


    data = request.get_json()
    dispute = Dispute(disputeID, **data)


    try:
        db.session.add(dispute)
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": {
                    "disputeID": disputeID
                },
                "message": "An error occurred creating the book."
            }
        ), 500


    return jsonify(
        {
            "code": 201,
            "data": dispute.json()
        }
    ), 201


if __name__ == '__main__':
    app.run(port=5000, debug=True)

