from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func, and_
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    name = Column(String)

class QuestResult(Base):
    __tablename__ = "quest_results"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # telegram_id
    quest_id = Column(String)  # 'quest_id' з questions.json
    user_name = Column(String)
    score = Column(Integer, default=0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Float)  # у секундах

# ----- СТВОРЕННЯ ТАБЛИЦЬ -----
def create_tables():
    Base.metadata.create_all(engine)

# ----- ФУНКЦІЇ ДЛЯ КВЕСТУ -----
def get_or_create_user(telegram_id, name):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, name=name)
        session.add(user)
        session.commit()
    elif user.name != name:
        user.name = name
        session.commit()
    session.close()
    return user

def start_quest_for_user(telegram_id, quest_id, user_name):
    session = Session()
    # Знайти існуючий запис
    result = session.query(QuestResult).filter_by(user_id=telegram_id, quest_id=quest_id).first()
    now = datetime.now()
    if result is None:
        result = QuestResult(
            user_id=telegram_id,
            quest_id=quest_id,
            user_name=user_name,
            score=0,
            start_time=now,
            end_time=None,
            duration=None
        )
        session.add(result)
    else:
        # Якщо проходить ще раз — оновити час та скинути результат
        result.score = 0
        result.start_time = now
        result.end_time = None
        result.duration = None
    session.commit()
    session.close()

def finish_quest_for_user(telegram_id, quest_id, score):
    session = Session()
    result = session.query(QuestResult).filter_by(user_id=telegram_id, quest_id=quest_id).first()
    if result and result.start_time:
        end_time = datetime.now()
        duration = (end_time - result.start_time).total_seconds()
        result.end_time = end_time
        result.duration = duration
        result.score = score
        session.commit()
    session.close()

def get_leaderboard_for_quest(quest_id, limit=10):
    session = Session()
    results = (
        session.query(QuestResult)
        .filter(
            and_(
                QuestResult.quest_id == quest_id,
                QuestResult.end_time != None
            )
        )
        .order_by(QuestResult.score.desc(), QuestResult.duration.asc())
        .limit(limit)
        .all()
    )
    leaderboard = []
    for res in results:
        leaderboard.append((res.user_name, res.score, res.duration))
    session.close()
    return leaderboard
