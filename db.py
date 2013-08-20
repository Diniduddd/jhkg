import os
from hashlib import sha512
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    username = Column(String, primary_key=True)
    passhash = Column(String)
    email = Column(String)
    school = Column(String)

    def __init__(self, username, password, email, school):
        # Store only a hashed password. Oh, and it's hashed with the username. lolol
        h = sha512(password)
        h.update(sha512(username).digest())
        self.username = username
        self.passhash = h.hexdigest()
        self.email = email
        self.school = school

    def __repr__(self):
        return "User('%s')" % (self.username)

def create_new_user(username, password, email, school=''):
    session = Session()

    # Check if user already exists
    userExists = session.query(User).filter(User.username == username).count()
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
    return Session().query(User).filter(User.username == username).first()

def verify_login(username, password):
    """ Returns true iff the given user/pass combo is valid. """
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    if user:
        pash = sha512(password)
        pash.update(sha512(username).digest())
        return user.passhash == pash.hexdigest()
    return False

def init_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
