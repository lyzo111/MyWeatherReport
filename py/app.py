from flask import Flask
from flask_mail import Mail
from db_model import db, User, Measurement
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

mail = Mail()

def create_app():
    app = Flask(__name__)

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Email config
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='your@email.com',
        MAIL_PASSWORD='your-password',
        MAIL_DEFAULT_SENDER='your@email.com'
    )

    db.init_app(app)
    mail.init_app(app)

    return app


app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create initial admin user if not exists
        if not User.query.filter_by(username="admin").first():
            user = User(
                username="admin",
                email="chrisus999@gmail.com"
            )
            user.set_password("secret123")  # hashed with werkzeug
            db.session.add(user)
            db.session.commit()

            measurement1 = Measurement(
                user_id=user.id,
                timestamp=datetime.now(timezone.utc),
                temperature=22.5,
                humidity=55,
                air_pressure=1013.2,
                location="living room"
            )
            measurement2 = Measurement(
                user_id=user.id,
                timestamp=datetime.now(timezone.utc),
                temperature=23.1,
                humidity=53,
                air_pressure=1012.8,
                location="bedroom"
            )

            db.session.add_all([measurement1, measurement2])
            db.session.commit()

    app.run(debug=True)
