import numpy as np
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Date, Text, func
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.orm import declarative_base, relationship

from schema.request import UpdateStarRequest

Base = declarative_base()

# 별(고인)
class Star(Base):
    __tablename__ = "star"

    star_id = Column(Integer, primary_key=True, index=True)
    star_name = Column(String(50), nullable=False)
    gender = Column(String(1), nullable=False)
    birth = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)
    relationship = Column(String(20), nullable=False)
    persona = Column(String(512), nullable=True)
    image = Column(String(512), nullable=True)
    chat_prompt_input_data = Column(Text, nullable=True)
    gpt_cond_latent_data = Column(MEDIUMBLOB, nullable=True)
    speaker_embedding_data = Column(MEDIUMBLOB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(String(50), ForeignKey("user.user_id"))

    @classmethod
    def create(cls, request: dict, chat_prompt_input_data: str, user_id: str) -> "Star":
        return cls(
            star_name=request["star_name"],
            gender=request["gender"],
            birth=request["birth"],
            death_date=request["death_date"],
            relationship=request["relationship"],
            persona=request["persona"],
            chat_prompt_input_data=chat_prompt_input_data,
            user_id=user_id
        )
    
    def update(self, request: UpdateStarRequest) -> "Star":
        self.star_name = request.star_name
        return self
    
    def insert_npy(
            self, 
            gpt_cond_latent_npy: np.ndarray, 
            speaker_embedding_npy: np.ndarray
        ):
        self.gpt_cond_latent_data = gpt_cond_latent_npy
        self.speaker_embedding_data = speaker_embedding_npy
        return self
        

# 회원
class User(Base): 
    __tablename__ = "user"

    user_id = Column(String(50), primary_key=True, index=True)
    password = Column(String(100), nullable=False)
    name = Column(String(50), nullable=True)
    phone = Column(String(15), nullable=True)
    birth = Column(Date)
    image = Column(String(256))
    policy_agreement_flag = Column(Boolean, nullable=False)
    payment_id = Column(String(12))
    credit = Column(Integer, nullable=False, default=0)
    user_type = Column(Integer, nullable=False, default=1)
    user_status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    stars = relationship("Star", lazy="joined")

    @classmethod
    def create(
        cls, 
        user_id: str, 
        hashed_password: str, 
        name: str, 
        phone: str,
        birth: Date,
        policy_agreement_flag: bool,
    ) -> "User":
        return cls(
            user_id=user_id,
            password=hashed_password,
            name=name,
            phone=phone,
            birth=birth,
            policy_agreement_flag=policy_agreement_flag,
        )
    
    def update(self, image: str) -> "User":
        self.image = image
        return self
    
    def update_password(self, hashed_password: str) -> "User":
        self.password = hashed_password
        return self
    
    def update_delete(self, new_status: int) -> "User":
        self.user_status = new_status
        return self


#관리자
class Admin(Base): 
    __tablename__ = "admin"

    admin_number = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(String(50), nullable=False)
    password = Column(String(100), nullable=False)
    name = Column(String(50), nullable=True)
    phone = Column(String(15), nullable=True)
    birth = Column(Date)
    admin_status = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    def create(
        cls, 
        admin_id: str, 
        hashed_password: str, 
        name: str, 
        phone: str,
        birth: Date,
    ) -> "Admin":
        return cls(
            admin_id=admin_id,
            password=hashed_password,
            name=name,
            phone=phone,
            birth=birth,
        )
