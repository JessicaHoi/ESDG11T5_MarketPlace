import os, threading
from dotenv import load_dotenv
from flask import Flask
from models import db
from routes import bp

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    from consumer import start_consumer
    t = threading.Thread(target=start_consumer, args=(app, db, __import__('models').Notification), daemon=True)
    t.start()

    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)