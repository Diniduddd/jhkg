import os
from collections import defaultdict
from hashlib import sha512
from sqlalchemy import Column, Integer, String, DateTime, Interval, ForeignKey, func, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
Base = declarative_base()

def uidify(string):
    return string.lower().replace(' ', '-')

# Stores user login and profile information.
class User(Base):
    __tablename__ = 'user'

    uid = Column(String, primary_key=True, index=True, unique=True)
    username = Column(String, index=True, unique=True)
    passhash = Column(String)
    email = Column(String, unique=True)
    school = Column(String)

    def __init__(self, username, password, email, school):
        self.uid = uidify(username)

        # Store only a hashed password. Oh, and it's hashed with the uid. lolol
        h = sha512(password)
        h.update(sha512(self.uid).digest())

        self.username = username

        self.passhash = h.hexdigest()
        self.email = email
        self.school = school

    def __repr__(self):
        return "User('%s')" % (self.uid)

# Stores contest data.
class Contest(Base):
    __tablename__ = 'contest'

    uid = Column(String, primary_key=True, index=True, unique=True)
    name = Column(String, index=True, unique=True)
    desc = Column(String)
    start_time = Column(DateTime, index=True)
    duration = Column(Interval)

    def __init__(self, name, desc, start_time, duration=timedelta(hours=3)):
        # In the UID, name is lowercased and spaces are replaced with dashes
        self.uid = uidify(name)
        self.name = name
        self.desc = desc
        self.start_time = start_time
        self.duration = duration

# Stores problems.
class Problem(Base):
    __tablename__ = 'problem'

    uid = Column(String, primary_key=True, index=True, unique=True)
    name = Column(String, index=True, unique=True)
    desc = Column(String)
    grader = Column(String)
    contest = Column(String, ForeignKey('contest.uid'), index=True)
    # Lower priority problems appear first.
    priority = Column(Integer)

    def __init__(self, name, desc, grader, contest, priority):
        # In the UID, name is lowercased and spaces are replaced with dashes
        self.uid = uidify(name)
        self.name = name
        self.desc = desc
        self.grader = grader
        self.contest = uidify(contest)
        self.priority = priority

# Stores which users have solved which problems.
class Solution(Base):
    __tablename__ = 'solution'

    user = Column(String, ForeignKey('user.uid'), primary_key=True, index=True)
    problem = Column(String, ForeignKey('problem.uid'), primary_key=True, index=True)
    score = Column(Integer)

    def __init__(self, user, problem, score):
        self.user = uidify(user)
        self.problem = uidify(problem)
        self.score = score

def create_new_user(username, password, email, school=''):
    session = Session()

    # Check for empty strings
    if not (username and password and email):
        return 'empty fields'

    # Check if user already exists
    userExists = get_user(username)
    emailExists = session.query(User).filter(func.lower(User.email) == func.lower(email)).count()

    if userExists:
        return 'user exists'
    elif emailExists:
        return 'email exists'
    
    new_user = User(username, password, email, school)
    session.add(new_user)
    session.commit()
    return 'success'

def get_all_users():
    return (u.username for u in Session().query(User).all())

def get_user(username):
    return Session().query(User).filter(User.uid == uidify(username)).first()

def verify_login(username, password):
    """ Returns true iff the given user/pass combo is valid. """
    session = Session()
    user = get_user(username)
    if user:
        pash = sha512(password)
        pash.update(sha512(user.uid).digest())
        return user.passhash == pash.hexdigest()
    return False

def get_contest_problems(contest_name):
    session = Session()
    probs = session.query(Problem).\
            filter(Problem.contest == uidify(contest_name)).\
            all()
    return probs

def get_current_contest():
    session = Session()
    now = datetime.utcnow()
    contest = session.query(Contest).\
              filter(now > Contest.start_time).\
              filter(now < Contest.start_time + timedelta(hours=3)).\
              first()
    if contest:
        return (contest, get_contest_problems(contest.name))
    else:
        return (None, None)

def get_upcoming_contests():
    session = Session()
    now = datetime.utcnow()
    contests = session.query(Contest).\
               filter(now < Contest.start_time + timedelta(hours=3)).\
               all()
    return contests or []

def get_all_contests():
    session = Session()
    contests = session.query(Contest).\
               all()
    return contests

def get_contest(name):
    session = Session()
    contest = session.query(Contest).\
              filter(Contest.uid == uidify(name)).\
              first()
    return contest

def new_contest(name, desc, start_time, duration=timedelta(hours=3)):
    """
    creates a new contest.
    start_time is a datetime
    """
    session = Session()
    new_contest = Contest(name, desc, start_time, duration=duration)
    session.add(new_contest)
    session.commit()
    return 'i tried'

def new_problem(name, desc, grader, contest='', priority=0):
    session = Session()
    new_problem = Problem(name, desc, grader, contest, priority)
    session.add(new_problem)
    session.commit()
    return 'success, maybe'

def get_problem(name):
    session = Session()
    prob = session.query(Problem).\
           filter(Problem.name == name).\
           first()
    return prob

def get_score(username, problem_name):
    result = Session().query(Solution).\
            filter(Solution.user == uidify(username)).\
            filter(Solution.problem == uidify(problem_name)).\
            first()
    if result:
        return result.score
    else:
        return 0

def get_all_scores():
    # we should probably cache this result TODO
    scores = defaultdict(int)
    for s in Session().query(Solution).all():
        scores[s.user] += s.score
    return scores

def set_score(username, problem_name, score):
    session = Session()
    cur_score = session.query(Solution).\
            filter(Solution.user == uidify(username)).\
            filter(Solution.problem == uidify(problem_name)).\
            first()
    if cur_score:
        # Don't let a lower score replace a higher one
        cur_score.score = max(cur_score.score, score)
    else:
        new_score = Solution(username, problem_name, score)
        session.add(new_score)
    session.commit()

def init_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def populate():
    """
    Populates the database with test data.
    """
    now = datetime.utcnow()
    create_new_user('admin', 'cakelyisgood', 'admin@admin.tk', school='MIT')
    create_new_user('testuser', 'user', 'user@user.tk', school='WCI')
    new_contest('Test contest', 'Just a test contest', now-timedelta(hours=1))
    new_contest('JHKG Round 0', 'The first ever JHKG contest. A "beta" for the actual thing.', datetime(2013, 10, 9, 19, 10, 0))
    #new_contest('JHKG Round 0', 'The first ever JHKG contest. A "beta" for the actual thing.', now+timedelta(minutes=1))
    #new_contest('JHKG 2013 Round 1', 'The first round in the JHKG High Koding Games', '2013-09-17 15:15')
    #new_contest('The Past Contest, Yo', 'This already happened!', '2012-09-17 15:15')
    new_problem('yolo', 'Submit anything to get full marks.', 'yolo', 'Test contest')
    new_problem('split sums', 'You will be given a text box with 100 positive integers. Their sum is below 2^32. You must compute their sum. You will have four minutes to paste their sum in the solution box.', 'splitsum', 'Test contest')
    new_problem('ASCII Triangle', '<a href="/problem/ascii-triangle">Problem description</a>', 'ascii_triangle', 'JHKG Round 0')
    new_problem('Viking Olympics', '<a href="/problem/viking-olympics">Problem description</a>', 'viking_olympics', 'JHKG Round 0')
