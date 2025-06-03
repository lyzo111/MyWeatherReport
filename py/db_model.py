from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()  # Create instance of SQLAlchemy


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def delete_user(self, password):
        """
            Deletes the user from the database if the provided password is correct.
            Returns True on success, False if password is incorrect.
        """
        if not self.check_password(password):
            return False

        db.session.delete(self)
        db.session.commit()
        return True


class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    air_pressure = db.Column(db.Float)
    location = db.Column(db.String(100))
