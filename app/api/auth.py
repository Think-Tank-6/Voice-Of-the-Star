from fastapi import APIRouter, Depends
from schema.response import UserSchema
from database.repository import AuthRepository
from database.orm import User
from service.auth import AuthService

from schema.request import JoinRequest


router = APIRouter(prefix="/auth")


@router.post("/join", status_code=201)
def user_join_handler(
    request: JoinRequest,
    auth_service: AuthService = Depends(),
    auth_repo: AuthRepository = Depends(),
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
    user: User = auth_repo.save_user(user=user)
    return UserSchema.from_orm(user)