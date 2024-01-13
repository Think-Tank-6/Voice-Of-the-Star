from fastapi import APIRouter, Depends, File, HTTPException, Body, UploadFile
from security import get_access_token
from schema.response import JWTResponse, UserSchema
from database.repository import UserRepository
from database.orm import User
from service.auth import AuthService
from schema.request import EmailCheckRequest, JoinRequest, LoginRequest, ModifyDeleteRequest, ModifyPasswordRequest
from starlette.status import HTTP_400_BAD_REQUEST
import requests
from pydantic import BaseModel


class KakaoLoginRequest(BaseModel):
    access_token: str

router = APIRouter(prefix="/users")
mypage_router = APIRouter(prefix="/mypage")


# 유저 검증 및 조회(공통)
def get_authenticated_user(
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
) -> User:
    return auth_service.verify_user(access_token=access_token, user_repo=user_repo)


@router.post("/join", status_code=201)
def user_join_handler(
    request: JoinRequest,
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
) -> UserSchema:
    hashed_password: str = auth_service.hash_password(
        plain_password=request.password
    )
    user: User = User.create(
        user_id=request.user_id, 
        hashed_password=hashed_password,
        name=request.name,
        phone=request.phone,
        birth=request.birth,
        policy_agreement_flag=request.policy_agreement_flag
    )
    user: User = user_repo.save_user(user=user)
    return UserSchema.from_orm(user)


@router.post("/join/email-check", status_code=200)
def email_check_handler(
    request: EmailCheckRequest,
    user_repo: UserRepository = Depends(),
):
    user: User = user_repo.get_user_by_user_id(user_id=request.input_email)
    
    if user:
        return {
            "status": "unavailable",
            "message": "Email is already in use.",
        }
    
    return {
            "status": "available",
            "message": "Email is available.",
        }
        

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

    if user.user_status != 1:
        raise HTTPException(status_code=403, detail="탈퇴한 회원입니다.")
    
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
            policy_agreement_flag=True
        )
        saved_user: User = auth_repo.save_user(user=new_user)
        access_token: str = auth_service.create_jwt(user_id=saved_user.user_id)
        return JWTResponse(access_token=access_token)
    else:
        existing_access_token: str = auth_service.create_jwt(user_id=user.user_id)
        return JWTResponse(access_token=existing_access_token)
    

@mypage_router.get("", status_code=200)
def get_user_handler(
    user: User = Depends(get_authenticated_user),
    user_repo: UserRepository = Depends(),
) -> UserSchema:
    
    user: User = user_repo.get_user_by_user_id(user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    return UserSchema.from_orm(user)


@mypage_router.patch("/modify-info", status_code=201)
def update_user_handler(
    image: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),
    user_repo: UserRepository = Depends(),
) -> UserSchema:
    
    user: User = user_repo.get_user_by_user_id(user.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    image_url = "test"
    user: User = user.update(image=image_url)
    user: User = user_repo.update_user(user=user)
    return UserSchema.from_orm(user)


@mypage_router.patch("/modify-password", status_code=201)
def modify_user_password_handler(
    request: ModifyPasswordRequest,
    user: User = Depends(get_authenticated_user),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends()
):
    
    verified: bool = auth_service.verify_password(
        plain_password=request.current_password,
        hash_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Not Authorized")
    
    hashed_password: str = auth_service.hash_password(
        plain_password=request.new_password
    )
    user: User = user.update_password(
        hashed_password=hashed_password,
    )
    user: User = user_repo.save_user(user=user)
    return UserSchema.from_orm(user)

@mypage_router.patch("/modify-delete", status_code=201)
def modify_user_delete_handler(
    request: ModifyDeleteRequest,
    user: User = Depends(get_authenticated_user),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends()
):
    # 현재 비밀번호 확인
    verified: bool = auth_service.verify_password(
        plain_password=request.current_password,
        hash_password=user.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="비밀번호가 다릅니다.")

    print("user_status:", user.user_status)
    # 사용자 상태를 업데이트 (예: 2로 변경)
    user.update_delete(new_status=2)

    # 변경된 사용자 정보 저장
    print("Updated user_status:", user.user_status)
    user = user_repo.save_user(user=user) 
    
    return UserSchema.from_orm(user)
