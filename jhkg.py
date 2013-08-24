# encoding=utf-8
import os
import random
import datetime
from flask import Flask, Markup, render_template, send_from_directory, redirect, session, request, g
import db

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

@app.before_request
def before_request():
    g.user = session.get('username')

# render_template with automatic value for username
def my_render_template(template_name, **kwargs):
    return render_template(template_name, username=g.user, **kwargs)

# Contest submission.
@app.route('/submit', methods=['POST'])
def contest_submission():
    submission = request.form["submission"]
    if submission.strip() == "16741364760":
        return my_render_template('contest.html', message='Correct!')
    else:
        return my_render_template('contest.html', message='That is probably wrong.')

# Registration POST action.
@app.route('/register_action', methods=['POST'])
def register_action():
    user = request.form["username"]
    email = request.form["email"]
    pswd = request.form["password"]
    school = request.form["school"] or 'summa cum laude from MIT'
    result = db.create_new_user(user, pswd, email, school)
    if result == 'user exists':
        return "That username already exists."
    elif result == 'email exists':
        return "Someone already registered with that email!"
    else: 
        return "Welcome to the club."

# Registration form.
@app.route('/register')
def register():
    return my_render_template('register.html')

# Login POST action.
@app.route('/login_action', methods=['POST'])
def login_action():
    user = request.form["username"]
    pswd = request.form["password"]

    if db.verify_login(user, pswd):
        session['username'] = user
        return redirect('/')
    else:
        return my_render_template('login.html', message="I don't recognize you.")

# Login form.
@app.route('/login')
def login():
    return my_render_template('login.html')

# Logout.
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# User profile.
@app.route('/user/<name>')
def profile(name):
    user = db.get_user(name)
    return my_render_template('profile.html', name=user.username, school=user.school)

# User list.
@app.route('/userlist')
def userlist():
    return my_render_template('userlist.html', userlist=db.get_all_users())

# Scoreboard.
@app.route('/scoreboard')
def scoreboard():
    fake_db_scores = {'かたわ'.decode('utf-8'):9000, 'Scrubmaster':69, 'Yolomeister':9001}
    # This converts the above dict into a list of triplets (rank, name, score).
    display_scores = [(i+1,u[0],u[1]) for i,u in enumerate(sorted(list(fake_db_scores.items()), key=lambda x:x[1], reverse=True))]
    return my_render_template('scoreboard.html', scores=display_scores)

# About.
@app.route('/about')
def about():
    return my_render_template('about.html')

# Index/home/login.
@app.route('/')
def index():
    if g.user:
        return my_render_template('contest.html')
    else:
        return my_render_template('home.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
