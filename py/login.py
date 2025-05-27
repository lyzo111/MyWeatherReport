from datetime import timedelta
from flask import Blueprint, request, session, redirect, url_for, current_app, render_template
from db_model import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

current_app.permanent_session_lifetime = timedelta(minutes=30)

@auth.route('/')
def index():
    if 'username' in session:
        username = session['username']
    else:
        username = None

    return render_template('index.html', username=username)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session['username'] = username
            return redirect(url_for('auth.index'))
        else:
            return 'Login failed. <a href="/login">Try again.</a>'

    return '''
    <form method="post">
        username: <input type="text" name="username"><br>
        password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    from db_model import db
    if 'username' in session:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if not username or not password or not email:
            return "All fields are required."

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return "Username already taken."

        is_first_user = User.query.count() == 0

        new_user = User(
            username=username,
            email=email,
            is_admin=is_first_user # First user is admin
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return '''
        <h2>Register</h2>
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Register">
        </form>
        '''
