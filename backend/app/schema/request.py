from fastapi import Form, UploadFile
from pydantic import BaseModel

from datetime import date
from typing import Optional


class JoinRequest(BaseModel):
    user_id: str
    password: str
    name: str
    phone: str
    birth: Optional[date]
    image: Optional[str]
    policy_agreement_flag: bool


class LoginRequest(BaseModel):
    user_id: str
    password: str
    

class CreateStarRequest(BaseModel):
    star_name: str
    gender: str
    birth: date
    death_date: date
    relationship: str
    persona: Optional[str]
    image: Optional[str]


class UpdateStarRequest(BaseModel):
    nickname: Optional[str]
    
    