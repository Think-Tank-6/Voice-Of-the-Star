from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

from schema.request import CreateStarRequest

Base = declarative_base()

class Star(Base):
    __tablename__ = "star"

    star_id = Column(Integer, primary_key=True, index=True)
    star_name = Column(String(50), nullable=False)
    gender = Column(String(1), nullable=False)
    birth = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)
    relationship = Column(String(20), nullable=False)
    persona = Column(String(512), nullable=True)
    image = Column(String(256), nullable=True)
    audio_file = Column(String(256), nullable=True)
    text_file = Column(String(256), nullable=True)

    @classmethod
    def create(cls, request: CreateStarRequest) -> "Star":
        return cls(
            star_name=request.star_name,
            gender=request.gender,
            birth=request.birth,
            death_date=request.death_date,
            relationship=request.relationship,
            persona=request.persona,
            image=request.image,
            audio_file=request.audio_file,
            text_file=request.text_file
        )
    
    def update(self, request: CreateStarRequest) -> "Star":
        self.star_name = request.star_name
        self.gender = request.gender
        self.birth = request.birth
        self.death_date = request.death_date
        self.relationship = request.relationship
        self.persona = request.persona
        self.image = request.image
        self.audio_file = request.audio_file
        self.text_file = request.text_file
        return self