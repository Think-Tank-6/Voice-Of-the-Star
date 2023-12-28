from pydantic import BaseModel


from datetime import date
from typing import Optional

# Data Example
# "star_id": 1,
# "star_name": "홍길동",
# "gender": "m",
# "birth": "1960-01-01",
# "death_date": "2020-01-01",
# "relationship": "아버지",
# "persona": "자상함",
# "audio_file": "(오디오파일 경로)",
# "text_file": "(텍스트파일 경로)",

class CreateStarRequest(BaseModel):
    star_name: str
    gender: Optional[str]
    birth: Optional[date]
    death_date: Optional[date]
    relationship: Optional[str]
    persona: Optional[str]
    image: Optional[str]
    audio_file: Optional[str]
    text_file: Optional[str]


class JoinRequest(BaseModel):
    user_id: str
    password: str
    name: str
    phone: str
    image: str
    policy_aggrement_flag: bool

