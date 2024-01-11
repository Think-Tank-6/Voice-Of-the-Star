from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.repository import UserRepository, AdminRepository
from service.auth import AuthService
from schema.request import AdminJoinRequest, AdminLoginRequest
from schema.response import AdminSchema,JWTResponse
from database.orm import Admin


router = APIRouter(prefix="/admin")

@router.get("/user-list")
def get_user_list(
    page: int = Query(1, alias="page"), 
    page_size: int = Query(8, alias="page_size"), 
    session: Session = Depends(get_db)
):
    user_repo = UserRepository(session)
    users, total = user_repo.get_users_paginated(page, page_size)
    return {"users": users, "total": total, "page": page, "page_size": page_size}


@router.get("/user-list/{user_id}")
def get_user_detail(user_id: str, session: Session = Depends(get_db)):
    user_repo = UserRepository(session)
    user = user_repo.get_user_by_user_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/join", status_code=201)
def user_join_handler(
    request: AdminJoinRequest,
    auth_service: AuthService = Depends(),
    admin_repo: AdminRepository = Depends(),
) -> AdminSchema:
    # 이미 존재하는 admin_id인지 확인
    existing_admin = admin_repo.get_admin_by_admin_id(request.admin_id)
    if existing_admin:
        raise HTTPException(status_code=400, detail="Member already exists")

    hashed_password: str = auth_service.hash_password(
        plain_password=request.password
    )
    admin: Admin = Admin.create(
        admin_id=request.admin_id, 
        hashed_password=hashed_password,
        name=request.name,
        phone=request.phone,
        birth=request.birth,
    )
    admin: admin = admin_repo.save_admin(admin=admin)
    return AdminSchema.from_orm(admin)

@router.get("/admin-list")
def get_admin_list(
    page: int = Query(1, alias="page"), 
    page_size: int = Query(8, alias="page_size"), 
    session: Session = Depends(get_db)
):
    admin_repo = AdminRepository(session)
    admins, total = admin_repo.get_admins_paginated(page, page_size)
    return {"admins": admins, "total": total, "page": page, "page_size": page_size}


@router.post("/login")
def admin_login_handler(
    request: AdminLoginRequest,
    auth_service: AuthService = Depends(),
    admin_repo: AdminRepository = Depends(),
):
    admin: Admin | None = admin_repo.get_admin_by_admin_id(
        admin_id=request.admin_id
    )
    if not admin:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    verified: bool = auth_service.verify_password(
        plain_password=request.password,
        hash_password=admin.password,
    )
    if not verified:
        raise HTTPException(status_code=401, detail="Not Authorized")
    
    access_token: str = auth_service.admincreate_jwt(admin_id=admin.admin_id)
    return JWTResponse(access_token=access_token)


