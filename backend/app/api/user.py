from fastapi import APIRouter, Depends, HTTPException
from security import get_access_token
from schema.response import JWTResponse, UserSchema
from database.repository import UserRepository
from database.orm import User
from service.auth import AuthService

from schema.request import JoinRequest, LoginRequest


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
        image=request.image,
        policy_aggrement_flag=request.policy_aggrement_flag
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