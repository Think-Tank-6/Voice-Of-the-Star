import bcrypt
from datetime import datetime, timedelta
from jose import jwt

class AuthService:
    encoding: str = "UTF-8"
    secret_key: str = "be2aed6fab97adc5116c8e844354b820530803d144f2c89858da20072ad74c80"
    jwt_algorithm = "HS256" # 웹토큰 생성에 사용되는 알고리즘

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
                "sub": user_id,
                "exp": datetime.now() + timedelta(days=1),  # 토큰의 만료시간 = 하루(요청한 시간부터)
            }, 
            self.secret_key, 
            algorithm=self.jwt_algorithm
        )
