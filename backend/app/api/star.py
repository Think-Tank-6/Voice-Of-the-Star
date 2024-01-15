from datetime import date
import os
from typing import List, Optional
from fastapi import Depends, File, Form, HTTPException, APIRouter, UploadFile
from service.auth import AuthService
from security import get_access_token

from database.orm import Star, User
from database.repository import UserRepository, StarRepository, MessageRepository, GptMessageRepository
from schema.request import CreateStarRequest
from schema.response import StarListSchema, StarSchema
from service.ai_serving import PromptGeneration, SpeakerIdentification, VoiceCloning

from io import BytesIO

import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/stars")

S3_BUCKET = os.getenv("S3_BUCKET")
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

if not aws_access_key_id or not aws_secret_access_key:
    raise NoCredentialsError

# AWS S3 클라이언트 초기화
s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

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
    print("last_message : ", last_message)
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
    
    print(type(original_voice_base64))

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
    selected_speaker_id: str = Form(...),
    speech_list: dict = Form(...),
    original_voice_base64: str = Form(...),
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)

    if not star: 
        raise HTTPException(status_code=404, detail="Star Not Found")

    speaker_identification = SpeakerIdentification()
    speaker_identification.save_star_voice(selected_speaker_id, speech_list, original_voice_base64)

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

# AWS S3에 파일을 업로드하는 함수입니다.
def upload_file_to_s3(file_stream, bucket, object_name):
    try:
        s3_client.upload_fileobj(file_stream, bucket, object_name)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload to S3")

# star image 수정 및 업로드
@router.patch("/{star_id}/uploadImage", status_code=200)
async def upload_img_star_handler(
    star_id: int, 
    file: UploadFile = File(...),
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(StarRepository),
) -> StarSchema:
    
    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")

    image_data = await file.read()
    object_name = f"star/{star_id}/{file.filename}"
    upload_file_to_s3(BytesIO(image_data), S3_BUCKET, object_name)

    # 파일 URL을 생성합니다. 's3://' 접두사를 포함하지 않는 버킷 이름을 사용합니다.
    file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{object_name}"
    
    star_repo.update_star_image_url(star_id=star_id, image_url=file_url)

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
    star_repo.delete_star(star_id=star_id)

