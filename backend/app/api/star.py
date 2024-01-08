from datetime import date
from typing import List, Optional
from fastapi import Depends, File, Form, HTTPException, APIRouter, UploadFile
from service.auth import AuthService
from security import get_access_token

from database.orm import Star, User
from database.repository import UserRepository, StarRepository
from schema.request import CreateStarRequest
from schema.response import StarListSchema, StarSchema
# from service.ai_serving import TextGeneration

router = APIRouter(prefix="/stars")


# 유저 검증 및 조회(공통)
def get_authenticated_user(
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
) -> User:
    return auth_service.verify_user(access_token=access_token, user_repo=user_repo)


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
async def create_star_handler(
    star_name: str = Form(...),
    gender: str = Form(...),
    birth: date = Form(...),
    death_date: date = Form(...),
    relationship: str = Form(...),
    persona: Optional[str] = Form(...),
    original_text_file: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    
    request = {
        "star_name": star_name,
        "gender": gender,
        "birth": birth,
        "death_date": death_date,
        "relationship": relationship,
        "persona": persona,
    }

    # Text Generation
    # text_generator = TextGeneration(request=request)
    # chat_prompt_input_data = text_generator.create_prompt_input()

    chat_prompt_input_data = "test"

    # DB Save
    star: Star = Star.create(
        request=request, 
        chat_prompt_input_data=chat_prompt_input_data,
        user_id=user.user_id
    )  
    star: Star = star_repo.create_star(star=star)

    return StarSchema.from_orm(star)


# star 생성(보이스 업로드)
@router.post("/voice-upload", status_code=200)
def upload_voice_handler(
    user: User = Depends(get_authenticated_user),  
) -> StarSchema:
    return {"message":"voice upload 페이지"}


# star 생성(보이스 선택)
@router.post("/voice-select", status_code=201)
def upload_voice_handler(
    user: User = Depends(get_authenticated_user),  
) -> StarSchema:
    return {"message":"voice select 페이지"}


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