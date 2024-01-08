from typing import List
from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database.connection import get_db, get_messages_collection
import datetime

from database.orm import Star, User, Room

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

    
class RoomRepository:
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_room_by_id(self, room_id: int) -> Room | None:
        return self.session.scalar(
            select(Room).where(Room.room_id == room_id)
        )

    def create_room(self, room: Room) -> Room:
        self.session.add(instance=room)
        self.session.commit()
        self.session.refresh(instance=room)
        return room
    
def save_message(room_id, user_id, star_id, message_text):
    messages_collection = get_messages_collection()
    message = {
        "room_id": room_id,
        "user_id": user_id,
        "star_id": star_id,
        "message": message_text,
        "created_at": datetime.datetime.utcnow()
    }
    result = messages_collection.insert_one(message)
    return result.inserted_id 