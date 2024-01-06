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



# class CreateStarRequest(BaseModel):
#     star_name:str = Form(...)
#     gender: str = Form(...)
#     birth: date = Form(...)
#     death_date: date = Form(...)
#     relationship: str = Form(...)
#     persona: Optional[str] = Form(...)
#     image: Optional[str] = Form(...)
#     text_file: Optional[UploadFile]