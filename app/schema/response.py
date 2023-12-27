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

    class Config:
        orm_mode = True

class StarListSchema(BaseModel):
    stars: List[StarSchema]