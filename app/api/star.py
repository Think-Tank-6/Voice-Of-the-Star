from typing import List
from fastapi import Depends, HTTPException, APIRouter

from database.orm import Star
from database.repository import StarRepository
from schema.request import CreateStarRequest
from schema.response import StarListSchema, StarSchema


router = APIRouter(prefix="/stars")


# 전체 star 조회
@router.get("", status_code=200)
def get_stars_handler(
    order: str | None = None,
    star_repo: StarRepository = Depends(StarRepository),  
) -> StarListSchema:
    stars: List[Star] = star_repo.get_stars()

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
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id)
    if star:
        return StarSchema.from_orm(star)
    raise HTTPException(status_code=404, detail="Star Not Found")


# star 생성
@router.post("", status_code=201)
def create_star_handler(
    request: CreateStarRequest,
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    star: Star = Star.create(request=request)  
    star: Star = star_repo.create_star(star=star)  
    return StarSchema.from_orm(star)    


# star 수정
@router.patch("/{star_id}", status_code=200)
def update_star_handler(
    star_id: int, 
    request: CreateStarRequest,
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id)
    if star:
        star: Star = star.update(request=request)
        star: Star = star_repo.update_star(star=star)
        return StarSchema.from_orm(star)
    return HTTPException(status_code=404, detail="Star Not Found")


# star 삭제
@router.delete("/{star_id}", status_code=204)
def delete_star_handler(
    star_id: int,
    star_repo: StarRepository = Depends(StarRepository),
):
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star Not Found")
    star_repo.delete_star(star_id=star_id)