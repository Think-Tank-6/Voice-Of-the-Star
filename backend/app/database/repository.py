from typing import List
from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database.connection import get_db, get_mongo
import datetime
from database.orm import Star, User, Admin
from pymongo import MongoClient


class StarRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_stars(self) -> List[Star]:  
        return list(self.session.scalars(select(Star)))  

    def get_star_by_star_id(self, star_id: int, user_id: str) -> Star | None:
        found_star : Star = self.session.scalar(
            select(Star).where(Star.star_id == star_id, Star.user_id == user_id)
        ) 
        return found_star

    def create_star(self, star: Star) -> Star:
        self.session.add(instance=star)  
        self.session.commit()   
        self.session.refresh(instance=star) 
        return star 
        
    def update_star(self, star: Star) -> Star:
        self.session.add(instance=star)
        self.session.commit()
        self.session.refresh(instance=star)
        return star

    def delete_star(self, star_id: int) -> None:
        self.session.execute(delete(Star).where(Star.star_id == star_id)) 
        self.session.commit()

class UserRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_user_by_user_id(self, user_id: str) -> User | None:
        return self.session.scalar(
            select(User).where(User.user_id == user_id)
        )

    def save_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()
        self.session.refresh(instance=user)
        return user
    
    def get_all_users(self):
        return self.session.query(User).all()
    
    def get_users_paginated(self, page: int, page_size: int):
        users = self.session.query(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        total = self.session.query(User).count()
        return users, total
    
    def update_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()
        self.session.refresh(instance=user)
        return user
    
    
class MessageRepository:
    def __init__(self):
        self.db = get_mongo()
        self.messages_collection = self.db['messages']

    def save_message(self, star_id, sender, content):
        message = {
            "sender": sender,
            "content": content,
            "created_at": datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        }
        
        # 해당 star_id의 문서를 찾고, 메시지 배열에 새 메시지를 추가
        result = self.messages_collection.update_one(
            {"star_id": star_id},
            {"$push": {"messages": message}},
            upsert=True
        )
        return result

    def get_last_message(self, star_id):
        last_message = self.messages_collection.find_one(
            {"star_id": star_id},
            sort=[("created_at", -1)]
        )
        return last_message
    
    def get_messages(self, star_id: int, limit: int) -> List[dict]:
        messages = self.messages_collection.aggregate([
            {"$match": {"star_id": star_id}},
            {"$unwind": "$messages"},
            {"$sort": {"messages.created_at": -1}},
            {"$limit": limit},
            {"$project": {"messages": 1}}
        ])
        return [msg["messages"] for msg in messages]
    
class GptMessageRepository:
    def __init__(self):
        self.db = get_mongo()
        self.gpt_messages_collection = self.db['gptmessages']
    
    def save_p_data(self, star_id, p_data):
        result = self.gpt_messages_collection.update_one(
            {"star_id": star_id},  # 'star_id'를 사용하여 특정 문서를 필터링합니다.
            {"$set": {"p_data": p_data}},  # 'p_data'를 업데이트합니다.
            upsert=True  # 해당 'star_id'가 없는 경우 새 문서를 만듭니다.
        )
        return result

    def get_gpt_message(self, star_id):
       # 'gpt_messages' 컬렉션에서 데이터 검색
        return self.gpt_messages_collection.find_one({"star_id": star_id})
    
    def get_p_data(self, star_id):
        return self.gpt_messages_collection.find_one({"star_id" : star_id})
    
    def save_gpt_message(self, star_id, sender, content):
        gpt_message = {
            "role": sender,
            "content": content
        }
        
        # 해당 star_id의 문서를 찾고, 메시지 배열에 새 메시지를 추가
        result = self.gpt_messages_collection.update_one(
            {"star_id": star_id},
            {"$push": {"messages": gpt_message}},
            upsert=True
        )
        return result

class AdminRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_admin_by_admin_id(self, admin_id: str) -> Admin | None:
        return self.session.query(Admin).filter(Admin.admin_id == admin_id).first()

    def save_admin(self, admin: Admin) -> Admin:
        self.session.add(admin)
        self.session.commit()
        self.session.refresh(admin)
        return admin
    
    def get_admins_paginated(self, page: int, page_size: int):
        admins = self.session.query(Admin).order_by(Admin.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        total = self.session.query(Admin).count()
        return admins, total
    
    def get_all_admins(self):
        return self.session.query(Admin).all()
    
    def get_admin_by_admin_id(self, admin_id: str) -> User | None:
        return self.session.scalar(
            select(Admin).where(Admin.admin_id == admin_id)
        )
