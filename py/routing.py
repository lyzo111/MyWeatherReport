from flask import Blueprint, request, session, redirect, url_for, render_template
from db_model import User, db
from werkzeug.security import check_password_hash


auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def index():
    if 'username' in session:
        username = session['username']
    else:
        username = None

    return render_template('index.html', username=username)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    error = None

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

    return render_template('login.html', error=error)


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    error = None

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

    return render_template('registration.html', error=error)
