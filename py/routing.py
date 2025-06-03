import csv
import json
from io import StringIO, TextIOWrapper
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, make_response
from db_model import User, Measurement, db
from datetime import datetime

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET', 'POST'])
def index():
    username = session.get('username')
    preview_data = session.get('csv_preview')
    live_data = session.get('live_data', [])  # ESP32 live data
    error = None
    success = None
    show_welcome = False

    user = None
    if username:
        user = User.query.filter_by(username=username).first()

    if request.method == 'POST':
        if 'file' in request.files:
            # CSV-Upload
            file = request.files['file']
            if file.filename:
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
            session.pop('csv_preview', None)
            success = f"{inserted} values saved. {duplicates} duplicates skipped."
            preview_data = None
        else:
            error = "Cannot save data."

    # Get filters from request
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc')
    location_filter = request.args.get('location', '')
    temp_min = request.args.get('temp_min', type=float)
    temp_max = request.args.get('temp_max', type=float)
    humidity_min = request.args.get('humidity_min', type=float)
    humidity_max = request.args.get('humidity_max', type=float)
    pressure_min = request.args.get('pressure_min', type=float)
    pressure_max = request.args.get('pressure_max', type=float)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    if user:
        # Build query with filters
        query = Measurement.query.filter_by(user_id=user.id)

        # Apply filters
        if location_filter:
            query = query.filter(Measurement.location.ilike(f'%{location_filter}%'))

        if temp_min is not None:
            query = query.filter(Measurement.temperature >= temp_min)
        if temp_max is not None:
            query = query.filter(Measurement.temperature <= temp_max)

        if humidity_min is not None:
            query = query.filter(Measurement.humidity >= humidity_min)
        if humidity_max is not None:
            query = query.filter(Measurement.humidity <= humidity_max)

        if pressure_min is not None:
            query = query.filter(Measurement.air_pressure >= pressure_min)
        if pressure_max is not None:
            query = query.filter(Measurement.air_pressure <= pressure_max)

        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
                query = query.filter(Measurement.timestamp >= date_from_dt)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
                query = query.filter(Measurement.timestamp <= date_to_dt)
            except ValueError:
                pass

        # Apply sorting
        if sort_by == 'timestamp':
            if sort_order == 'asc':
                query = query.order_by(Measurement.timestamp.asc())
            else:
                query = query.order_by(Measurement.timestamp.desc())
        elif sort_by == 'location':
            if sort_order == 'asc':
                query = query.order_by(Measurement.location.asc())
            else:
                query = query.order_by(Measurement.location.desc())
        else:  # default to id
            if sort_order == 'asc':
                query = query.order_by(Measurement.id.asc())
            else:
                query = query.order_by(Measurement.id.desc())

        measurements = query.all()
        locations = sorted(set(m.location for m in Measurement.query.filter_by(user_id=user.id).all()))

        # Check if this is right after login
        if session.get('just_logged_in'):
            show_welcome = True
            session.pop('just_logged_in', None)
    else:
        measurements = []
        locations = []

    return render_template(
        'index.html',
        username=username,
        measurements=measurements,
        preview_data=preview_data,
        live_data=live_data,
        error=error,
        success=success,
        locations=locations,
        show_welcome=show_welcome,
        # Filter values for form
        current_filters={
            'sort_by': sort_by,
            'sort_order': sort_order,
            'location': location_filter,
            'temp_min': temp_min,
            'temp_max': temp_max,
            'humidity_min': humidity_min,
            'humidity_max': humidity_max,
            'pressure_min': pressure_min,
            'pressure_max': pressure_max,
            'date_from': date_from,
            'date_to': date_to
        }
    )


@auth.route('/esp32/data', methods=['POST'])
def receive_esp32_data():
    """Endpoint for ESP32 to send live data"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['timestamp', 'temperature', 'humidity', 'air_pressure', 'location']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Store in session for display (live data, not saved to DB)
        live_data = session.get('live_data', [])

        # Add new data point
        live_data.append({
            'timestamp': data['timestamp'],
            'temperature': float(data['temperature']),
            'humidity': float(data['humidity']),
            'air_pressure': float(data['air_pressure']),
            'location': data['location']
        })

        # Keep only last 50 live data points
        if len(live_data) > 50:
            live_data = live_data[-50:]

        session['live_data'] = live_data

        return jsonify({'status': 'success', 'message': 'Data received'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@auth.route('/api/live-data')
def get_live_data():
    """API endpoint to get current live data"""
    live_data = session.get('live_data', [])
    return jsonify(live_data)


@auth.route('/clear-live-data', methods=['POST'])
def clear_live_data():
    """Clear live data from session"""
    session.pop('live_data', None)
    return redirect(url_for('auth.index'))


@auth.route('/discard-preview', methods=['POST'])
def discard_preview():
    """Remove CSV preview from session"""
    session.pop('csv_preview', None)
    return jsonify({'status': 'success'})


@auth.route('/export/csv')
def export_csv():
    """Export user's measurements as CSV"""
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('auth.login'))

    # Get current filters to apply them to export
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc')
    location_filter = request.args.get('location', '')
    temp_min = request.args.get('temp_min', type=float)
    temp_max = request.args.get('temp_max', type=float)
    humidity_min = request.args.get('humidity_min', type=float)
    humidity_max = request.args.get('humidity_max', type=float)
    pressure_min = request.args.get('pressure_min', type=float)
    pressure_max = request.args.get('pressure_max', type=float)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Build filtered query (same logic as in index route)
    query = Measurement.query.filter_by(user_id=user.id)

    # Apply filters
    if location_filter:
        query = query.filter(Measurement.location.ilike(f'%{location_filter}%'))
    if temp_min is not None:
        query = query.filter(Measurement.temperature >= temp_min)
    if temp_max is not None:
        query = query.filter(Measurement.temperature <= temp_max)
    if humidity_min is not None:
        query = query.filter(Measurement.humidity >= humidity_min)
    if humidity_max is not None:
        query = query.filter(Measurement.humidity <= humidity_max)
    if pressure_min is not None:
        query = query.filter(Measurement.air_pressure >= pressure_min)
    if pressure_max is not None:
        query = query.filter(Measurement.air_pressure <= pressure_max)
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(Measurement.timestamp >= date_from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(Measurement.timestamp <= date_to_dt)
        except ValueError:
            pass

    # Apply sorting
    if sort_by == 'timestamp':
        if sort_order == 'asc':
            query = query.order_by(Measurement.timestamp.asc())
        else:
            query = query.order_by(Measurement.timestamp.desc())
    elif sort_by == 'location':
        if sort_order == 'asc':
            query = query.order_by(Measurement.location.asc())
        else:
            query = query.order_by(Measurement.location.desc())
    else:  # default to id
        if sort_order == 'asc':
            query = query.order_by(Measurement.id.asc())
        else:
            query = query.order_by(Measurement.id.desc())

    measurements = query.all()

    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(['id', 'timestamp', 'temperature', 'humidity', 'air_pressure', 'location'])

    # Write data
    for m in measurements:
        writer.writerow([
            m.id,
            m.timestamp.isoformat(),
            m.temperature,
            m.humidity,
            m.air_pressure,
            m.location
        ])

    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=weather_data_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return response


@auth.route('/export/json')
def export_json():
    """Export user's measurements as JSON"""
    username = session.get('username')
    if not username:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('auth.login'))

    # Get current filters to apply them to export (same logic as CSV export)
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'desc')
    location_filter = request.args.get('location', '')
    temp_min = request.args.get('temp_min', type=float)
    temp_max = request.args.get('temp_max', type=float)
    humidity_min = request.args.get('humidity_min', type=float)
    humidity_max = request.args.get('humidity_max', type=float)
    pressure_min = request.args.get('pressure_min', type=float)
    pressure_max = request.args.get('pressure_max', type=float)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Build filtered query (same logic as in index route)
    query = Measurement.query.filter_by(user_id=user.id)

    # Apply filters (same as CSV export)
    if location_filter:
        query = query.filter(Measurement.location.ilike(f'%{location_filter}%'))
    if temp_min is not None:
        query = query.filter(Measurement.temperature >= temp_min)
    if temp_max is not None:
        query = query.filter(Measurement.temperature <= temp_max)
    if humidity_min is not None:
        query = query.filter(Measurement.humidity >= humidity_min)
    if humidity_max is not None:
        query = query.filter(Measurement.humidity <= humidity_max)
    if pressure_min is not None:
        query = query.filter(Measurement.air_pressure >= pressure_min)
    if pressure_max is not None:
        query = query.filter(Measurement.air_pressure <= pressure_max)
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.filter(Measurement.timestamp >= date_from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to)
            query = query.filter(Measurement.timestamp <= date_to_dt)
        except ValueError:
            pass

    # Apply sorting (same as CSV export)
    if sort_by == 'timestamp':
        if sort_order == 'asc':
            query = query.order_by(Measurement.timestamp.asc())
        else:
            query = query.order_by(Measurement.timestamp.desc())
    elif sort_by == 'location':
        if sort_order == 'asc':
            query = query.order_by(Measurement.location.asc())
        else:
            query = query.order_by(Measurement.location.desc())
    else:  # default to id
        if sort_order == 'asc':
            query = query.order_by(Measurement.id.asc())
        else:
            query = query.order_by(Measurement.id.desc())

    measurements = query.all()

    # Create JSON data
    data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'user': username,
            'total_records': len(measurements),
            'filters_applied': {
                'sort_by': sort_by,
                'sort_order': sort_order,
                'location': location_filter,
                'temperature_range': [temp_min, temp_max],
                'humidity_range': [humidity_min, humidity_max],
                'pressure_range': [pressure_min, pressure_max],
                'date_range': [date_from, date_to]
            }
        },
        'measurements': []
    }

    # Add measurements data
    for m in measurements:
        data['measurements'].append({
            'id': m.id,
            'timestamp': m.timestamp.isoformat(),
            'temperature': m.temperature,
            'humidity': m.humidity,
            'air_pressure': m.air_pressure,
            'location': m.location
        })

    # Create response
    response = make_response(json.dumps(data, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers[
        'Content-Disposition'] = f'attachment; filename=weather_data_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    return response


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
            session['just_logged_in'] = True  # Flag for welcome message
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
                is_admin=is_first_user  # First user is admin
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('auth.login'))

    return render_template('registration.html', error=error, username=username)