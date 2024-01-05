from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()
MYSQL_URL = os.getenv("MYSQL_URL")

engine = create_engine(MYSQL_URL)
SeesionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB 설정
MONGO_URI = os.getenv('MONGO_URI')
mongo_client = MongoClient(MONGO_URI)

def get_db():
    session = SeesionFactory()
    try:
        yield session
    finally:
        session.close()
        
# 데이터베이스와 컬렉션 선택
def get_mongo():
    db = mongo_client['chat_database']
    return db

def get_messages_collection():
    db = get_mongo()
    return db['messages']