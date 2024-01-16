from datetime import date
import json
import os
from typing import List, Optional
from fastapi import Depends, File, Form, HTTPException, APIRouter, UploadFile , Path
from service.s3_service import S3Service, get_s3_service
from service.auth import AuthService
from security import get_access_token

from database.orm import Star, User
from database.repository import UserRepository, StarRepository, MessageRepository, GptMessageRepository
from schema.request import UpdateStarRequest, voiceSelectRequest
from schema.response import StarListSchema, StarSchema
from service.ai_serving import PromptGeneration, SpeakerIdentification, VoiceCloning


from io import BytesIO

from dotenv import load_dotenv

load_dotenv()

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


# 마지막 채팅 불러오기
@router.get("/{star_id}/last", status_code=200)
def get_last_message(
    star_id: int, 
    chat_repo: MessageRepository = Depends()
):
    last_message = chat_repo.get_last_message(star_id)
    return last_message


# 단일 star 조회
@router.get("/{star_id}", status_code=200)
def get_star_handler(
    star_id: int,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)

    if not star:
        raise HTTPException(status_code=404, detail="Star Not Found")
    return StarSchema.from_orm(star)


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
    gptmessage_repo : GptMessageRepository = Depends(GptMessageRepository)
) -> StarSchema:
    
    request = {
        "star_name": star_name,
        "gender": gender,
        "birth": birth,
        "death_date": death_date,
        "relationship": relationship,
        "persona": persona,
    }
    

    # Open text file
    original_text = await original_text_file.read()
    original_text = original_text.decode("utf-8")

    # Prompt Generation
    prompt_generator = PromptGeneration(request,original_text)
    chat_prompt_input_data = prompt_generator.create_prompt_input()

    # DB Save
    star: Star = Star.create(
        request=request, 
        chat_prompt_input_data=chat_prompt_input_data,
        user_id=user.user_id
    )  
    star: Star = star_repo.create_star(star=star)
    
    gptmessage_repo.save_p_data(star_id=star.star_id, p_data=chat_prompt_input_data)

    return StarSchema.from_orm(star)


# star 생성(보이스 업로드)
@router.post("/voice-upload", status_code=200)
def upload_voice_handler(
    original_voice_file: UploadFile = File(...),
    user: User = Depends(get_authenticated_user)
    ):
    speaker_identification = SpeakerIdentification()
    speaker_num, full_speech_list, speaker_sample_list,original_voice_base64 = speaker_identification.get_speaker_samples(original_voice_file)
    

    extracted_voice_info = {
        "speaker_num":speaker_num, 
        "full_speech_list":full_speech_list, 
        "speaker_sample_list":speaker_sample_list,
        "original_voice_base64":original_voice_base64
        }
    
    return extracted_voice_info


# star 생성(보이스 선택)
@router.post("/voice-select/{star_id}", status_code=201)
def upload_voice_handler(
    star_id: int,
    # request: voiceSelectRequest,
    selected_speaker_id: str = Form(...),
    speech_list: str = Form(...),
    original_voice_base64: str = Form(...),
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(),
) -> StarSchema:
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    if not star: 
        raise HTTPException(status_code=404, detail="Star Not Found")
    speech_list_dict = json.loads(speech_list)
   
    speaker_identification = SpeakerIdentification()
    # print("request: ", request)
    speaker_identification.save_star_voice(selected_speaker_id, speech_list_dict, original_voice_base64,star_id)
    voice_cloning = VoiceCloning()
    gpt_cond_latent_pkl, speaker_embedding_pkl = voice_cloning.get_star_voice_vector(
        star_id=star_id
    )
    
    # npy 테스트 필요
    star: Star = star.insert_npy(
        gpt_cond_latent_npy=gpt_cond_latent_pkl, 
        speaker_embedding_npy=speaker_embedding_pkl
    )
    # DB save
    star: Star = star_repo.update_star(star=star)

    return StarSchema.from_orm(star)


# star 수정
@router.patch("/{star_id}", status_code=200)
def update_star_handler(
    star_id: int, 
    request: UpdateStarRequest,
    user: User = Depends(get_authenticated_user),   # 유저 검증 dependency
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    if star:
        star: Star = star.update(request=request)
        star: Star = star_repo.update_star(star=star)
        return StarSchema.from_orm(star)
    return HTTPException(status_code=404, detail="Star Not Found")


# star image 수정 및 업로드
@router.patch("/{star_id}/uploadImage", status_code=200)
async def upload_img_star_handler(
    star_id: int, 
    file: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(StarRepository),
    s3: S3Service = Depends(get_s3_service),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    image_data = await file.read()
    object_name = f"star/{star_id}/{file.filename}"
    
    s3.upload_file_to_s3(file_stream=BytesIO(image_data), object_name=object_name)
    image_url = f"https://{s3.S3_BUCKET}.s3.amazonaws.com/{object_name}"

    star_repo.update_star_image_url(star_id=star_id, image_url=image_url)

    updated_star: Star = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    return StarSchema.from_orm(updated_star)


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
    # MongoDB에서 관련 데이터 삭제
    star_repo.delete_star_mongo(star_id=star_id)

    # 기존 SQL 데이터베이스에서 별 삭제
    star_repo.delete_star(star_id=star_id)

