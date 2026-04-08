import os
from dotenv import load_dotenv
from flask import Flask
from models import db
from routes import bp

# ── Reads .env file and loads variables into environment ─────────────────────
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db was created in models.py, it needs to be connected to the app here via db.init_app(app)
# bp is a Flask Blueprint defined in routes.py, they need to be registered here via app.register_blueprint(bp)
db.init_app(app)
app.register_blueprint(bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)