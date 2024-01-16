from io import BytesIO
from fastapi import APIRouter, Depends, File, HTTPException, Body, UploadFile
from service.s3_service import S3Service, get_s3_service
from security import get_access_token
from schema.response import JWTResponse, UserSchema
from database.repository import UserRepository
from database.orm import User
from service.auth import AuthService
from schema.request import EmailCheckRequest, JoinRequest, LoginRequest, ModifyDeleteRequest, ModifyPasswordRequest, KakaoLoginRequest
from service.s3_service import S3Service
import requests


router = APIRouter(prefix="/users")
mypage_router = APIRouter(prefix="/mypage")


# 유저 검증 및 조회(공통)
def get_authenticated_user(
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
) -> User:
    return auth_service.verify_user(access_token=access_token, user_repo=user_repo)


# 유저 회원가입
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


# 이메일 중복 체크
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
        

# 유저 로그인
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
        raise HTTPException(status_code=403, detail="Not activated User")
    
    access_token: str = auth_service.create_jwt(user_id=user.user_id)
    return JWTResponse(access_token=access_token)


# 유저 카카오 로그인
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
    

# 마이페이지 조회
@mypage_router.get("", status_code=200)
def get_user_handler(
    user: User = Depends(get_authenticated_user),
    user_repo: UserRepository = Depends(),
) -> UserSchema:
    
    user: User = user_repo.get_user_by_user_id(user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    return UserSchema.from_orm(user)


# 마이페이지 - 개인정보 수정
@mypage_router.patch("/modify-info", status_code=201)
async def update_user_handler(
    image: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),
    user_repo: UserRepository = Depends(),
    s3: S3Service = Depends(get_s3_service),
) -> UserSchema:
    
    user: User = user_repo.get_user_by_user_id(user.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    image_data = await image.read()
    object_name = f"user/{user.user_id}/{image.filename}"

    # S3 업로드
    s3.upload_file_to_s3(file_stream=BytesIO(image_data), object_name=object_name)
    image_url = f"https://{s3.S3_BUCKET}.s3.amazonaws.com/{object_name}"

    user: User = user.update(image=image_url)
    user: User = user_repo.update_user(user=user)
    return UserSchema.from_orm(user)


# 마이페이지 - 비밀번호 변경
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


# 마이페이지 - 회원탈퇴
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

    # 사용자 상태를 업데이트(2로 변경)
    user.update_delete(new_status=2)
    user = user_repo.save_user(user=user) 
    return UserSchema.from_orm(user)
