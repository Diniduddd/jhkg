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

# Stores each user's completed problems (temporary) TODO
# problem_name in done_problem[user] iff user finished problem_name
done_problem = defaultdict(set)

# Time utils for jinja2 templates.
# These all take a datetime.

# Converts time into user's local timezone.
def localtime(t):
    return t-g.timezone
app.jinja_env.globals['localtime'] = localtime

# Pretty formatting of date and time
@app.template_filter('prettydate')
def prettydate(d):
    return d.strftime('%A %B %d, %Y')
@app.template_filter('prettytime')
def prettytime(t):
    # Remove leading zeroes too
    return t.strftime('%I:%M %p').lstrip('0')
@app.template_filter('prettydatetime')
def prettydatetime(dt):
    return '%s, %s' % (prettytime(dt), prettydate(dt))

@app.before_request
def before_request():
    g.user = session.get('username')

    # Get timezone from cookie
    utc_delta_sec = int(request.cookies.get('timezone') or '0')
    g.timezone = timedelta(minutes=utc_delta_sec)

# render_template with automatic value for username
def my_render_template(template_name, **kwargs):
    return render_template(template_name, username=g.user, now=datetime.utcnow(), **kwargs)

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
    return my_render_template('profile.html', user=user)

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

# A certain contest.
@app.route('/contest/<contest_name>')
def show_contest(contest_name):
    contest = db.get_contest(contest_name)
    problems = db.get_contest_problems(contest_name)
    end_time = contest.start_time + contest.duration
    return my_render_template('contest.html',
            contest = contest,
            problems = [(i+1,p) for i,p in enumerate(problems)],
            user_solved = done_problem[g.user],
            end_time = end_time)

# Contest.
@app.route('/contests')
def contest():
    contests = db.get_all_contests()
    now = datetime.utcnow()
    past_contests = sorted([c for c in contests if c.start_time + c.duration < now], key=lambda c:c.start_time, reverse=True)
    upcoming_contests = sorted([c for c in contests if c.start_time > now], key=lambda c:c.start_time)
    current_contests = [c for c in contests if c.start_time < now and c.start_time + c.duration > now]
    return my_render_template('contest_list.html',
            current_contests = current_contests,
            upcoming_contests = upcoming_contests,
            past_contests = past_contests
            )

# Contest data request.
@app.route('/contest_data', methods=['POST'])
def contest_data():
    problem = request.form["problem"]
    grader_name = db.get_problem(problem).grader
    gen = getattr(inputgen, grader_name)()
    given_data[g.user] = gen
    given_time[g.user] = datetime.utcnow()
    return gen

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
