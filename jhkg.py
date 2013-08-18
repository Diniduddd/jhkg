# encoding=utf-8
import os
import random
import datetime
from flask import Flask, Markup, render_template, send_from_directory, redirect, session, request, g

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

# Login POST.
@app.route('/login', methods=['POST'])
def login():
    user = request.form["username"]
    pswd = request.form["password"]

    # Currently allow any username with the password "cake".
    if pswd == "cake":
        session['username'] = user
        return redirect('/')
    else:
        return my_render_template('login.html', message='Wrong password. Try "cake".')

# Logout.
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# Index/home!
@app.route('/')
def index():
    if g.user:
        return my_render_template('contest.html')
    else:
        return my_render_template('login.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
