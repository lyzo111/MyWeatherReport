from flask import Flask
from db_model import db


def create_app():
    app = Flask(__name__)

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app


app = create_app()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
