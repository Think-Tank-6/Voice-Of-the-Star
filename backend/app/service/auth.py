import bcrypt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from jose import jwt
from dotenv import load_dotenv
import os
from database.orm import User, Admin
from database.repository import UserRepository, AdminRepository
from security import get_access_token

load_dotenv()

class AuthService:
    encoding: str = "UTF-8"
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM") # 웹토큰 생성에 사용되는 알고리즘

    def hash_password(self, plain_password: str) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding), 
            salt=bcrypt.gensalt()
        )
        return hashed_password.decode(self.encoding)
    
    def verify_password(self, plain_password: str, hash_password: str) -> bool:
        return bcrypt.checkpw(  # checkpw의 결과 리턴(True, False)
            plain_password.encode(self.encoding),
            hash_password.encode(self.encoding)
        )
    
    def create_jwt(self, user_id: str) -> str: 
        return jwt.encode(
            {
                "user_id": user_id,
                "exp": datetime.now() + timedelta(days=1),  # 토큰의 만료시간 = 하루(요청한 시간부터)
            }, 
            self.SECRET_KEY, 
            algorithm=self.JWT_ALGORITHM
        )
    
    def decode_jwt(self, access_token: str) -> str:
        payload: dict = jwt.decode(
            access_token, 
            self.SECRET_KEY, 
            algorithms=[self.JWT_ALGORITHM]
        )
        return payload["user_id"]   # user_id 리턴
    
    def verify_user(
            self, 
            access_token: str = Depends(get_access_token),
            user_repo: UserRepository = Depends(),
        ) -> User:

        # 유저 검증
        user_id: str = self.decode_jwt(access_token=access_token)

        # 유저 조회
        user: User | None = user_repo.get_user_by_user_id(user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        
        return user
    
    def admincreate_jwt(self, admin_id: str) -> str: 
        return jwt.encode(
            {
                "admin_id": admin_id,
                "exp": datetime.now() + timedelta(days=1),  # 토큰의 만료시간 = 하루(요청한 시간부터)
            }, 
            self.SECRET_KEY, 
            algorithm=self.JWT_ALGORITHM
        )
    
    def admindecode_jwt(self, access_token: str) -> str:
        payload: dict = jwt.decode(
            access_token, 
            self.SECRET_KEY, 
            algorithms=[self.JWT_ALGORITHM]
        )
        return payload["admin_id"]   # user_id 리턴
    
    def verify_admin(
            self, 
            access_token: str = Depends(get_access_token),
            admin_repo: AdminRepository = Depends(),
        ) -> Admin:

        # 유저 검증
        admin_id: str = self.decode_jwt(access_token=access_token)

        # 유저 조회
        admin: User | None = admin_repo.get_admin_by_admin_id(adin_id=admin_id)
        if not admin:
            raise HTTPException(status_code=404, detail="User Not Found")
        
        return admin
        
    

