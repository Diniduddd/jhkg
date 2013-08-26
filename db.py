import os
from hashlib import sha512
from sqlalchemy import Column, Integer, String, DateTime, Interval, ForeignKey, func, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Stores user login and profile information.
class User(Base):
    __tablename__ = 'user'

    username = Column(String, primary_key=True)
    passhash = Column(String)
    email = Column(String, unique=True)
    school = Column(String)

    def __init__(self, username, password, email, school):
        # Store only a hashed password. Oh, and it's hashed with the username. lolol
        h = sha512(password)
        h.update(sha512(username.lower()).digest())

        # Lowercase username for case insensitive login
        self.username = username.lower()

        self.passhash = h.hexdigest()
        self.email = email
        self.school = school

    def __repr__(self):
        return "User('%s')" % (self.username)

# Stores contest data.
class Contest(Base):
    __tablename__ = 'contest'

    name = Column(String, primary_key=True, unique=True)
    desc = Column(String)
    start_time = Column(DateTime, index=True)
    duration = Column(Interval)

    def __init__(self, name, desc, start_time, duration=timedelta(hours=3)):
        self.name = name
        self.desc = desc
        self.start_time = start_time
        self.duration = duration

# Stores problems.
class Problem(Base):
    __tablename__ = 'problem'

    name = Column(String, primary_key=True)
    desc = Column(String)
    grader = Column(String)
    contest = Column(String, ForeignKey('contest.name'), index=True)
    # Lower priority problems appear first.
    priority = Column(Integer)

    def __init__(self, name, desc, grader, contest, priority):
        self.name = name
        self.desc = desc
        self.grader = grader
        self.contest = contest
        self.priority = priority

def create_new_user(username, password, email, school=''):
    session = Session()

    # Check for empty strings
    if not (username and password and email):
        return 'empty fields'

    # Check if user already exists
    userExists = session.query(User).filter(User.username == username.lower()).count()
    emailExists = session.query(User).filter(User.email == email).count()

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
    return Session().query(User).filter(User.username == username.lower()).first()

def verify_login(username, password):
    """ Returns true iff the given user/pass combo is valid. """
    session = Session()
    user = session.query(User).filter(User.username == username.lower()).first()
    if user:
        pash = sha512(password)
        pash.update(sha512(username.lower()).digest())
        return user.passhash == pash.hexdigest()
    return False

def get_contest_problems(name):
    session = Session()
    probs = session.query(Problem).\
            filter(Problem.contest == name).\
            all()
    return probs

def get_current_contest():
    session = Session()
    now = datetime.now()
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
    now = datetime.now()
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
              filter(Contest.name == name).\
              first()
    return contest

def new_contest(name, desc, start_time):
    """
    creates a new contest.
    start_time is a string in the format "yyyy-mm-dd hh:mm"
    """
    session = Session()
    start_time_datetime = datetime(*map(int, start_time.replace('-', ' ').replace(':', ' ').split()))
    new_contest = Contest(name, desc, start_time_datetime)
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

def init_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def populate():
    """
    Populates the database with test data.
    """
    now = datetime.now()
    create_new_user('admin', 'admin', 'admin@admin.tk', school='MIT')
    new_contest('IOI Live Now', 'Brave The Seas With IOI Live NoW!', (now-timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'))
    new_contest('IOI Qualification Round 1', 'IOI 2014 Qualification Round 1', (now+timedelta(hours=1, minutes=15)).strftime('%Y-%m-%d %H:%M'))
    new_contest('JHKG 2013 Round 1', 'The first round in the JHKG High Koding Games', '2013-09-17 15:15')
    new_contest('The Past Contest, Yo', 'This already happened!', '2012-09-17 15:15')
    new_problem('yolo', 'Just YOLO!', 'yolo', 'IOI Live Now')
    new_problem('split sums', 'Add up 100 positive integers. Will fit into a long int.', 'splitsum', 'IOI Live Now')
