import csv
from io import TextIOWrapper
from flask import Blueprint, request, session, redirect, url_for, render_template
from db_model import User, db


auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def index():
    from db_model import Measurement
    from datetime import datetime, timezone


    username = session.get('username')
    preview_data = session.get('csv_preview')
    measurements = []
    error = None
    success = None

    user = None
    if username:
        user = User.query.filter_by(username=username).first()

    if request.method == 'POST':
        if 'file' in request.files:
            # CSV-Upload
            file = request.files['file']
            reader = csv.DictReader(TextIOWrapper(file, encoding='utf-8'))

            preview_data = []
            for row in reader:
                try:
                    preview_data.append({
                    'timestamp': row['timestamp'],
                    'temperature': float(row['temperature']),
                    'humidity': float(row['humidity']),
                    'air_pressure': float(row['air_pressure']),
                    'location': row['location']
                    })
                except Exception as e:
                    print(f"Error processing row {row}: {e}")
            session['csv_preview'] = preview_data

        elif 'session_csv' in request.form and username:
            # Save CSV data to database
            inserted = 0
            duplicates = 0
            if preview_data:
                for row in preview_data:
                    ts = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                    exists = Measurement.query.filter_by(
                        timestamp=ts,
                        location=row['location'],
                        user_id=user.id
                    ).first()
                    if not exists:
                        m = Measurement(
                            timestamp=ts,
                            temperature=row['temperature'],
                            humidity=row['humidity'],
                            air_pressure=row['air_pressure'],
                            location=row['location'],
                            user_id=user.id
                        )
                        db.session.add(m)
                        inserted += 1
                    else:
                        duplicates += 1
            db.session.commit()
            session.pop('csv_preview')
            success = f"{inserted} values saved. {duplicates} duplicates skipped."
            preview_data = None
        else:
            error = "Cannot save data."

    if user:
        measurements = Measurement.query.filter_by(user_id=user.id).order_by(Measurement.id.desc()).all()

    return render_template(
        'index.html',
        username=username,
        measurements=measurements,
        preview_data=preview_data,
        error=error,
        success=success
    )

@auth.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    username = ''

    if 'username' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.permanent = True
            session['username'] = username
            return redirect(url_for('auth.index'))
        elif not username or not password:
            error = 'All fields are required.'
        else:
            error = 'Entered credentials do not belong to any account. Try again or register.'

    return render_template('login.html', error=error, username=username)


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    username = ''

    if 'username' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            error = "All fields are required."

        if 0 < len(password) < 6 and username:
            error = "Password must be at least 6 characters long."

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            error = "Username already taken."

        if error is None:
            is_first_user = User.query.count() == 0

            new_user = User(
                username=username,
                is_admin=is_first_user # First user is admin
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('auth.login'))

    return render_template('registration.html', error=error, username=username)
