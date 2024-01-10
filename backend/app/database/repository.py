from typing import List
from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database.connection import get_db, get_messages_collection, get_gpt_messages_collection
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
    
    def update_user(self, user: User) -> User:
        self.session.add(instance=user)
        self.session.commit()
        self.session.refresh(instance=user)
        return user

    
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
    
    
class MessageRepository:
    def __init__(self, messages_collection = Depends(get_messages_collection)):
        self.messages_collection = messages_collection

    def save_message(self, room_id, sender, content):
        message = {
            "sender": sender,
            "content": content,
            "created_at": datetime.datetime.utcnow()
        }
        
        # 해당 room_id의 문서를 찾고, 메시지 배열에 새 메시지를 추가
        result = self.messages_collection.update_one(
            {"room_id": room_id},
            {"$push": {"messages": message}},
            upsert=True
        )
        return result

    def get_last_message(self, room_id):
        last_message = self.messages_collection.find_one(
            {"room_id": room_id},
            sort=[("created_at", -1)]
        )
        return last_message
    
    def get_room_info(self, room_id: int):
        """
        특정 채팅방의 정보를 가져옵니다.
        :param room_id: 채팅방 ID
        :return: 채팅방 정보 (사용자 ID와 챗봇 ID 포함)
        """
        # 이 부분은 실제 데이터베이스 쿼리로 대체해야 합니다.
        # 예시 코드는 가상의 채팅방 정보를 반환합니다.
        room_info = self.session.scalar(
            select(Room).where(Room.room_id == room_id)
        )
        if room_info:
            return {
                "room_id": room_info.room_id,
                "room_name": room_info.room_name,
                "user_id": room_info.user_id,
                "star_id": room_info.star_id,
                "image_data": room_info.image_data,
                "created_at": room_info.created_at
            }
        else:
            return None
    
    def get_messages(self, room_id: int, limit: int) -> List[dict]:
        """
        특정 채팅방의 최근 채팅 메시지를 가져옵니다.
        :param room_id: 채팅방 ID
        :param limit: 반환할 메시지의 최대 개수
        :return: 채팅 메시지 리스트
        """
        return list(self.messages_collection.find({"room_id": room_id}).sort("created_at", -1).limit(limit))
    
class GptMessageRepository:
    def __init__(self, messages_collection = Depends(get_gpt_messages_collection)):
        self.messages_collection = messages_collection
    
    def save_gpt_message(self, star_id, sender, content):
        gpt_message = {
            "sender": sender,
            "content": content,
            "created_at": datetime.datetime.utcnow()
        }
        
        # 해당 room_id의 문서를 찾고, 메시지 배열에 새 메시지를 추가
        result = self.messages_collection.update_one(
            {"star_id": star_id},
            {"$push": {"messages": gpt_message}},
            upsert=True
        )
        
        return result

    def get_gpt_message(self, gpt_data_id):
       # 'gpt_messages' 컬렉션에서 데이터 검색
        return self.messages_collection.find_one({"gpt_data_id": gpt_data_id})