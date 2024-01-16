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
    star_name: Optional[str]


class ModifyPasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ModifyDeleteRequest(BaseModel):
    current_password: str
    user_status: str


class AdminJoinRequest(BaseModel):
    admin_id: str
    password: str
    name: str
    phone: str
    birth: date

class AdminLoginRequest(BaseModel):
    admin_id: str
    password: str
    

class PlayVoiceRequest(BaseModel):
    text: str

class voiceSelectRequest(BaseModel):
    selected_speaker_id: str
    speech_list: str
    original_voice_base64: str