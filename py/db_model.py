from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy() # Create instance of SQLAlchemy

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)

    measurements = db.relationship('Measurement', backref='user', lazy=True)

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    air_pressure = db.Column(db.Float)

