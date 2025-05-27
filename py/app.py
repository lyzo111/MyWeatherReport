import os.path
from flask import Flask
from db_model import db
from login import auth
from datetime import timedelta

def create_app():
    app = Flask(__name__, template_folder=os.path.abspath('../templates'))

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

    db.init_app(app)
    app.register_blueprint(auth)
    return app


app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
