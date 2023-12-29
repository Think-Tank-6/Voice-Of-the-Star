from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class StarSchema(BaseModel):
    star_id: int
    star_name: str
    gender: Optional[str]
    birth: Optional[date]
    death_date: Optional[date]
    relationship: Optional[str]
    persona: Optional[str]
    image: Optional[str]
    audio_file: Optional[str]
    text_file: Optional[str]

    # ORM 객체를 pydantic으로 변환하기 위한 옵션
    class Config:
        orm_mode = True


class StarListSchema(BaseModel):
    stars: List[StarSchema]


class UserSchema(BaseModel):
    user_id: str
    name: str
    phone: str
    image: str
    policy_aggrement_flag: bool

    class Config:
        orm_mode = True


class JWTResponse(BaseModel):
    access_token: str
