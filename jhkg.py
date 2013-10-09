# encoding=utf-8
import os
import random
import datetime
from collections import defaultdict
from flask import Flask, Markup, render_template, send_from_directory, redirect, session, request, g
import db
from db import uidify
from datetime import datetime, timedelta
import problems
from markdown import markdown

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

admins = {'admin'}

# Stores the data that we gave each user.
given_data = {}
# Stores the seed that we gave each user.
given_seed = {}
# Stores the time at which the data were given.
given_time = {}

# Time utils for jinja2 templates.
# These all take a datetime.

# Converts time into user's local timezone.
def localtime(t):
    return t-g.timezone
app.jinja_env.globals['localtime'] = localtime

# Converts time from user's local timezone.
def from_localtime(t):
    return t+g.timezone

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

# Replacing spaces with dashes for e.g. javascript
app.jinja_env.filters['uidify'] = uidify

@app.before_request
def before_request():
    g.user = session.get('username')

    # Get timezone from cookie
    utc_delta_sec = int(request.cookies.get('timezone') or '0')
    g.timezone = timedelta(minutes=utc_delta_sec)

    # time of request
    g.now = datetime.utcnow()

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
    scores = db.get_all_scores()
    # This converts the above dict into a list of triplets (rank, name, score).
    display_scores = [(i+1,u[0],u[1]) for i,u in enumerate(sorted(list(scores.items()), key=lambda x:x[1], reverse=True))]
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
        return my_render_template('admin_newproblem.html',
                contests=contests,
                graders=problems.problem_list)
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
    start_time = datetime(*map(int, start_time.replace('-', ' ').replace(':', ' ').split()))
    start_time = from_localtime(start_time)
    db.new_contest(name, desc, start_time)
    return redirect('/admin')

# A certain contest.
@app.route('/contest/<contest_name>')
def show_contest(contest_name):
    contest = db.get_contest(contest_name)
    if contest:
        problems = db.get_contest_problems(contest_name)
        if g.user:
            user_solved = { p.name:db.get_score(g.user, p.name) for p in problems }
        else:
            user_solved = {}
        end_time = contest.start_time + contest.duration
        return my_render_template('contest.html',
                contest = contest,
                problems = [(i+1,p) for i,p in enumerate(problems)],
                user_solved = user_solved,
                end_time = end_time)
    else:
        return page_not_found()

# Contest.
@app.route('/contests')
def contest():
    contests = db.get_all_contests()
    past_contests = sorted([c for c in contests if c.start_time + c.duration < g.now], key=lambda c:c.start_time, reverse=True)
    upcoming_contests = sorted([c for c in contests if c.start_time > g.now], key=lambda c:c.start_time)
    current_contests = [c for c in contests if c.start_time < g.now and c.start_time + c.duration > g.now]
    return my_render_template('contest_list.html',
            current_contests = current_contests,
            upcoming_contests = upcoming_contests,
            past_contests = past_contests
            )

# Contest data request.
@app.route('/contest_data', methods=['POST'])
def contest_data():
    problem = db.get_problem(request.form["problem"])
    if problem:
        grader_name = problem.grader
        data, seed = getattr(problems, grader_name).generate()
        given_data[g.user] = data
        given_seed[g.user] = seed
        given_time[g.user] = g.now
        return data
    else:
        return "I don't know that problem, dude."

# Contest submission.
@app.route('/contest_submit', methods=['POST'])
def contest_submission():
    problem_name = request.form["problem"]
    submission = request.form["submission"]
    problem = db.get_problem(problem_name)
    if problem:
        problem_name = problem.grader
        gr_func = getattr(problems, problem_name).verify
        base_score = gr_func(given_data[g.user], given_seed[g.user], submission)
        if base_score:
            # They were right!
            # Add bonus points for time
            contest = db.get_contest(problem.contest)
            if g.now < contest.start_time + contest.duration:
                # Contest is still ongoing; give them points!
                time_elapsed = g.now - contest.start_time
                time_bonus = round(100-100*(time_elapsed.total_seconds()/contest.duration.total_seconds()))
                db.set_score(g.user, problem.uid, base_score+time_bonus)
                return 'Well done. You got %d points and a time bonus of %d!' % (base_score, time_bonus)
            else:
                return 'Well done. This contest is over, but you would have gotten %d points!' % base_score
        else:
            return 'Incorrect. Keep trying!'
    else:
        return 'What exactly are you trying to do?'

# Page for individual problems.
@app.route('/problem/<problem_name>')
def show_problem(problem_name):
    try:
        safe_name = "".join(c for c in problem_name if c.isalnum() or c in "-").rstrip()
        prob_file = open('problems/%s' % safe_name)
        problem = markdown(prob_file.read().decode('utf-8'))
        prob_file.close()
        return my_render_template('problem.html', problem=problem)
    except IOError:
        return page_not_found()

# Home.
@app.route('/')
def index():
    return my_render_template('home.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
