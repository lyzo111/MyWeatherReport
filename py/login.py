from datetime import timedelta

from flask import Flask, request, session, redirect, url_for

app = Flask(__name__)
# from login import something

app.secret_key = '''Rahmp! Di, tsu-ga-mm-gi-guk, gi
Guga fli-gu-gi-gu, ga fli-gu-gi-gu, d-dee-ee
Yu-gu-guk di, yu-go-go-gu-gu-ga-be
Fli-gu-gi-gu, a-fli-gu-gi-ga whoo-ma-mama'''
app.permanent_session_lifetime = timedelta(minutes=30)

# Dummy user db -> remove?
USERS = {
    'admin': 'admin123',
    'donero': 'ewedon'
}

@app.route('/')
def index():
    if 'username' in session:
        return f"Hello {session['username']}! <br><a href='/logout'>Logout</a>"
    return 'Not logged in. <a href="/login">Login</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USERS and USERS[username] == password:
            session.permanent = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Login fehlgeschlagen. <a href="/login">Nochmal versuchen</a>'

    # GET: show login form
    return '''
    <form method="post">
        Benutzername: <input type="text" name="username"><br>
        Passwort: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
