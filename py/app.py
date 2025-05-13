from flask import Flask
from db_model import db, User, Measurement
from datetime import datetime, timezone
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'  # Replace with database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # Initialize database with Flask app

with app.app_context():
    db.create_all()  # Create tables

    user = User(username="admin", password="secret123", email="chrisus999@gmail.com")
    db.session.add(user)
    db.session.commit()

    # Add location data to database later!
    measurement1 = Measurement(
        user_id=user.id,
        timestamp=datetime.now(timezone.utc),
        temperature=22.5,
        humidity=55,
        air_pressure=1013.2
    )
    measurement2 = Measurement(
        user_id=user.id,
        timestamp=datetime.now(timezone.utc),
        temperature=23.1,
        humidity=53,
        air_pressure=1012.8
    )

    db.session.add_all([measurement1, measurement2])
    db.session.commit()

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
