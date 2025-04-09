from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

# Set up database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    score = Column(Integer, default=0)

# Create tables
Base.metadata.create_all(bind=engine)

def get_or_create_user(user_id, user_name):
    """Retrieve a user or create if not exists."""
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=user_name)
        session.add(user)
        session.commit()
    return user

def update_score(user_id, score):
    """Update the user's score."""
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if user and score > user.score:
        user.score = score
        session.commit()

def get_leaderboard():
    """Get the leaderboard sorted by score."""
    session = SessionLocal()
    users = session.query(User).order_by(User.score.desc()).all()
    return [(user.name, user.score) for user in users]