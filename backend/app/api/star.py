from typing import List
from fastapi import Depends, HTTPException, APIRouter
from service.auth import AuthService
from security import get_access_token

from database.orm import Star, User
from database.repository import AuthRepository, StarRepository
from schema.request import CreateStarRequest
from schema.response import StarListSchema, StarSchema


router = APIRouter(prefix="/stars")


# 유저 검증 및 조회(공통)
def get_authenticated_user(
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(),
    auth_repo: AuthRepository = Depends(),
) -> User:
    return auth_service.verify_user(access_token=access_token, auth_repo=auth_repo)


# 전체 star 조회
@router.get("", status_code=200)
def get_stars_handler(
    order: str | None = None,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
) -> StarListSchema:
    
    stars: List[Star] = user.stars

    if order and order == "DESC":
        return StarListSchema(
            stars=[StarSchema.from_orm(star) for star in stars[::-1]]  
        )
    return StarListSchema(
        stars=[StarSchema.from_orm(star) for star in stars] 
    )


# 단일 star 조회
@router.get("/{star_id}", status_code=200)
def get_star_handler(
    star_id: int,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)

    if star:
        return StarSchema.from_orm(star)
    raise HTTPException(status_code=404, detail="Star Not Found")


# star 생성
@router.post("", status_code=201)
def create_star_handler(
    request: CreateStarRequest,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    
    star: Star = Star.create(request=request, user_id=user.user_id)  
    star: Star = star_repo.create_star(star=star)  
    return StarSchema.from_orm(star)


# star 수정
@router.patch("/{star_id}", status_code=200)
def update_star_handler(
    star_id: int, 
    request: CreateStarRequest,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)

    if star:
        star: Star = star.update(request=request)
        star: Star = star_repo.update_star(star=star)
        return StarSchema.from_orm(star)
    return HTTPException(status_code=404, detail="Star Not Found")


# star 삭제
@router.delete("/{star_id}", status_code=204)
def delete_star_handler(
    star_id: int,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(StarRepository),
):
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    
    if not star:
        raise HTTPException(status_code=404, detail="Star Not Found")
    star_repo.delete_star(star_id=star_id)