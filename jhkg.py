# encoding=utf-8
import os
import random
import datetime
from collections import defaultdict
from flask import Flask, Markup, render_template, send_from_directory, redirect, session, request, g
import db
from datetime import datetime, timedelta
import inputgen
import graders

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

admins = {'admin'}

# Stores the data that we gave each user.
given_data = {}
# Stores the time at which the data were given.
given_time = {}

# Stores each user's completed problems (temporary)
# problem_name in done_problem[user] iff user finished problem_name
done_problem = defaultdict(set)

@app.before_request
def before_request():
    g.user = session.get('username')

# render_template with automatic value for username
def my_render_template(template_name, **kwargs):
    return render_template(template_name, username=g.user, **kwargs)

@app.errorhandler(404)
def page_not_found(e=None):
    return my_render_template('404.html'), 404

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
    elif result == 'empty fields':
        return "Please fill in all required fields."
    elif result == 'success': 
        return "Welcome to the club."
    else:
        return result

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

# Admin panel.
@app.route('/admin')
def admin():
    if g.user in admins:
        return my_render_template('admin.html')
    else:
        return page_not_found()

@app.route('/admin/new_problem')
def admin_newproblem():
    if g.user in admins:
        contests = db.get_upcoming_contests()
        return my_render_template('admin_newproblem.html', contests=contests)
    else:
        return page_not_found()

@app.route('/admin/new_problem/action', methods=['POST'])
def admin_newproblem_action():
    if g.user not in admins:
        return page_not_found()
    name = request.form["name"]
    desc = request.form["description"]
    grader = request.form["grader"]
    contest = request.form["contest"]
    priority = request.form["priority"]
    db.new_problem(name, desc, grader, contest, priority)
    return redirect('/admin')

@app.route('/admin/new_contest')
def admin_newcontest():
    if g.user in admins:
        return my_render_template('admin_newcontest.html')
    else:
        return page_not_found()

@app.route('/admin/new_contest/action', methods=['POST'])
def admin_newcontest_action():
    if g.user not in admins:
        return page_not_found()
    name = request.form["name"]
    desc = request.form["description"]
    start_time = request.form["start_time"]
    db.new_contest(name, desc, start_time)
    return redirect('/admin')

# Contest.
@app.route('/contest')
def contest():
    # Show them contest info!
    current_contest, problems = db.get_current_contest()
    if current_contest:
        return my_render_template('contest.html',
                contest = current_contest,
                end_time = current_contest.start_time + timedelta(hours=3),
                problems=problems,
                user_solved = done_problem[g.user])
    else:
        upcoming_contests = db.get_upcoming_contests()
        return my_render_template('upcoming_contests.html', contests=upcoming_contests, now=datetime.now())

# Contest data request.
@app.route('/contest_data', methods=['POST'])
def contest_data():
    problem = request.form["problem"]
    grader_name = db.get_problem(problem).grader
    gen = getattr(inputgen, grader_name)
    given_data[g.user] = gen
    given_time[g.user] = datetime.now()
    return gen()

# Contest submission.
@app.route('/contest_submit', methods=['POST'])
def contest_submission():
    problem = request.form["problem"]
    submission = request.form["submission"]
    grader_name = db.get_problem(problem).grader

    gr_func = getattr(graders, grader_name)
    if gr_func(given_data[g.user], submission):
        # They were right!
        done_problem[g.user].add(problem)
        return 'Correct!'

    return 'Incorrect.'

# Page for individual problems.
#@app.route('/problem/<problem_name>')
#def show_problem(problem_name):
#    problem = db.get_problem(problem_name)
#    return my_render_template('problem.html', problem=problem)

# Home.
@app.route('/')
def index():
    return my_render_template('home.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
