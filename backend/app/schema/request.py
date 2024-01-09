from pydantic import BaseModel

from datetime import date
from typing import Optional


class JoinRequest(BaseModel):
    user_id: str
    password: str
    name: str
    phone: str
    birth: date
    policy_agreement_flag: bool


class EmailCheckRequest(BaseModel):
    input_email: str


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


class ModifyPasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    