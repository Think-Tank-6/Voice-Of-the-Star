from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel

class StarSchema(BaseModel):
    star_id: int
    star_name: str
    gender: str
    birth: date
    death_date: date
    relationship: str
    persona: Optional[str]
    original_audio_file: Optional[str]
    original_text_file: str

    # ORM 객체를 pydantic으로 변환하기 위한 옵션
    class Config:
        orm_mode = True


class StarListSchema(BaseModel):
    stars: List[StarSchema]


class UserSchema(BaseModel):
    user_id: str
    name: str
    phone: str
    policy_agreement_flag: bool
    birth: date
    image: str
    policy_agreement_flag: bool
    user_type: int
    user_status: int
    created_at: datetime

    class Config:
        orm_mode = True


class JWTResponse(BaseModel):
    access_token: str
