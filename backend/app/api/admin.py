from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.repository import UserRepository


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