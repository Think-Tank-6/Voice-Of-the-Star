from fastapi import APIRouter, Depends, HTTPException, Body
from security import get_access_token
from schema.response import JWTResponse, UserSchema
from database.repository import UserRepository
from database.orm import User
from service.auth import AuthService
from schema.request import JoinRequest, LoginRequest
from starlette.status import HTTP_400_BAD_REQUEST
import requests
from pydantic import BaseModel


class KakaoLoginRequest(BaseModel):
    access_token: str

router = APIRouter(prefix="/users")


@router.post("/join", status_code=201)
def user_join_handler(
    request: JoinRequest,
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
):
    hashed_password: str = auth_service.hash_password(
        plain_password=request.password
    )
    user: User = User.create(
        user_id=request.user_id, 
        hashed_password=hashed_password,
        name=request.name,
        phone=request.phone,
        birth=request.birth,
        image=request.image,
        policy_agreement_flag=request.policy_agreement_flag
    )
    user: User = user_repo.save_user(user=user)
    return UserSchema.from_orm(user)


@router.post("/login")
def user_login_handler(
    request: LoginRequest,
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
):
    user: User | None = user_repo.get_user_by_user_id(
        user_id=request.user_id
    )
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    verified: bool = auth_service.verify_password(
        plain_password=request.password,
        hash_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Not Authorized")
    
    access_token: str = auth_service.create_jwt(user_id=user.user_id)
    return JWTResponse(access_token=access_token)

@router.post("/kakao-login")
def kakao_login_handler(
    kakao_login_request: KakaoLoginRequest = Body(...),
    auth_service: AuthService = Depends(),
    auth_repo: UserRepository = Depends(),
):
    KAKAO_TOKEN_VALIDATION_URL = 'https://kapi.kakao.com/v2/user/me'
    headers = {"Authorization": f"Bearer {kakao_login_request.access_token}"}
    kakao_response = requests.get(KAKAO_TOKEN_VALIDATION_URL, headers=headers)
    
    if kakao_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid kakao token")

    kakao_user_info = kakao_response.json()
    print("Kakao API Response:", kakao_user_info)

    # 카카오 API 응답에서 정보 가져오기
    user_id = kakao_user_info.get("kakao_account", {}).get("email")
    name = kakao_user_info.get("kakao_account", {}).get("name")
    phone_number = kakao_user_info.get("kakao_account", {}).get("phone_number")
    birthday = kakao_user_info.get("kakao_account", {}).get("birthday")  # 예: "1231"
    birthyear = kakao_user_info.get("kakao_account", {}).get("birthyear")  # 예: "1990"
    
    if birthday and birthyear:
        birth = f"{birthyear}-{birthday[:2]}-{birthday[2:]}"
    else:
        birth = None


    user: User | None = auth_repo.get_user_by_user_id(user_id=user_id)

    if not user:
        new_user = User.create(
            user_id=user_id,
            hashed_password=auth_service.hash_password(plain_password="default_password"),
            name=name,
            phone=phone_number,
            birth=birth,
            image=None,
            policy_agreement_flag=True
        )
        saved_user: User = auth_repo.save_user(user=new_user)
        access_token: str = auth_service.create_jwt(user_id=saved_user.user_id)
        return JWTResponse(access_token=access_token)
    else:
        existing_access_token: str = auth_service.create_jwt(user_id=user.user_id)
        return JWTResponse(access_token=existing_access_token)