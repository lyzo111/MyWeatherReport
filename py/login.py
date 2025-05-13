from datetime import timedelta
from flask import Blueprint, request, session, redirect, url_for, current_app
from db_model import User
import hashlib

auth = Blueprint('auth', __name__)

@auth.before_app_first_request
def setup_session_settings():
    current_app.secret_key = '''Rahmp! Di, tsu-ga-mm-gi-guk, gi
Guga fli-gu-gi-gu, ga fli-gu-gi-gu, d-dee-ee
Yu-gu-guk di, yu-go-go-gu-gu-ga-be
Fli-gu-gi-gu, a-fli-gu-gi-ga whoo-ma-mama'''
    current_app.permanent_session_lifetime = timedelta(minutes=30)

def hash_password_sha256(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@auth.route('/')
def index():
    if 'username' in session:
        return f"Hello {session['username']}! <br><a href='/logout'>Logout</a>"
    return 'Not logged in. <a href="/login">Login</a>'

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_input = hash_password_sha256(password)

        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == hashed_input:
            session.permanent = True
            session['username'] = username
            return redirect(url_for('auth.index'))
        else:
            return 'Login fehlgeschlagen. <a href="/login">Nochmal versuchen</a>'

    return '''
    <form method="post">
        Benutzername: <input type="text" name="username"><br>
        Passwort: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))
