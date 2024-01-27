import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import torchaudio
from ai_models.voice_cloning.xtts import inference
from service.s3_service import S3Service
from schema.request import PlayVoiceRequest
from database.repository import MessageRepository, GptMessageRepository, StarRepository, UserRepository
from service.auth import HTTPException, AuthService
from service.s3_service import S3Service, get_s3_service
import json
import logging
from service.ai_serving import voice_cloning_model, ChatGeneration, DetectCrime
from security import get_access_token
from database.orm import Star, User
from dotenv import load_dotenv
import pickle


from service.auth import AuthService
import sys
import os


load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/chat")

# get path
audio_dir_path = os.getenv("AUDIO_DIR_PATH")
voice_phishing_p_data_path = os.getenv("VOICE_PHISHING_PROMPT_PATH")

# create DetectCrime instance
detect_crime = DetectCrime(voice_phishing_p_data_path)


# 유저 검증 및 조회(공통)
def get_authenticated_user(
    access_token: str = Depends(get_access_token),
    auth_service: AuthService = Depends(),
    user_repo: UserRepository = Depends(),
) -> User:
    return auth_service.verify_user(access_token=access_token, user_repo=user_repo)


class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, star_id: int):
        self.active_connections[star_id] = websocket

    def disconnect(self, star_id: int):
        del self.active_connections[star_id]

    async def send_message(self, sender: str, message: str, star_id: int):
        message_to_send = {"sender": sender, "content": message}
        await self.active_connections[star_id].send_text(json.dumps(message_to_send))

manager = ConnectionManager()
message_repo = MessageRepository()
gpt_message_repo = GptMessageRepository()
user_input = ""


# 최근 채팅 메시지 조회
@router.get("/{star_id}/messages")
async def get_chat_messages(
    star_id: int, 
    limit: int = 50 # limit: 반환할 메시지의 최대 개수
):
    try:
        messages = message_repo.get_messages(star_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages for star {star_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching messages")


# WebSocket
@router.websocket("/{star_id}")
async def websocket_endpoint(
        websocket: WebSocket, 
        star_id: int
    ):

    #p_data 가져오기 (수정필요)
    p_data = gpt_message_repo.get_p_data(star_id)
    
    # p_data가 None이거나 "messages" 키가 없는 경우, 빈 리스트로 처리
    if p_data is not None and "messages" in p_data:
        gpt_input_list = p_data["messages"]
    else:
        gpt_input_list = []
    
    chat_generation = ChatGeneration(p_data, gpt_input_list)
    # 현재 채팅 내역 
    full_message_list = []
    
    # 연결 수락 및 처리
    await websocket.accept()
    await manager.connect(websocket, star_id)

    try:
        sys.setrecursionlimit(10000)
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # 메시지 형식 검증
                if not all(k in message_data for k in ("content",)):
                    logger.error("Invalid message format")
                    continue
                
                # user의 메시지
                user_input = message_data['content']

                if detect_crime.detect_voice_phishing_activity(user_input):
                    response = "의심스러운 메시지가 감지되었습니다. 다시 메시지를 전송해주세요."
                else:
                    # GPT 모델을 사용하여 응답 생성
                    # gpt 내에서 자동으로 user_input, gpt_response 저장
                    gpt_response, _ = chat_generation.get_gpt_answer(user_input)
                    response = gpt_response
                    full_message_list.append({"user_input": user_input,"gpt_response":gpt_response})

                await manager.send_message("assistant", response, star_id)

            except json.JSONDecodeError:
                logger.error("Error decoding message")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for user: {star_id}")
        
        for current_message in full_message_list:
            current_user_input = current_message["user_input"]
            current_gpt_response = current_message["gpt_response"]

            # 메시지 저장 로직: MessageRepository에 사용자 응답 저장
            message_repo.save_message(star_id=star_id, sender="user", content=current_user_input)

            # 메시지 저장 로직: MessageRepository에 gpt 응답 저장
            message_repo.save_message(star_id=star_id, sender="assistant", content=current_gpt_response)

            # GptMessageRepository에 사용자 응답 저장
            gpt_message_repo.save_gpt_message(star_id=star_id, sender="user", content=current_user_input)

            # GptMessageRepository에 gpt 응답 저장
            gpt_message_repo.save_gpt_message(star_id=star_id, sender="assistant", content=current_gpt_response)

        manager.disconnect(star_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        await websocket.close(code=1011) 
        

# Voice Cloning
@router.post("/play-voice/{star_id}", status_code=200)
async def play_voice_handler(
    star_id: int,
    request: PlayVoiceRequest,
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(),
    s3: S3Service = Depends(get_s3_service),
):
    text = request.text

    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)
    
    if not star:
        raise HTTPException(status_code=404, detail="Star Not Found")
    
    # Star 데이터베이스의 gpt_cond_latent, speaker_embedding (.pkl 파일) 조회
    gpt_cond_latent_data = star.gpt_cond_latent_data
    speaker_embedding_data = star.speaker_embedding_data
    
    gpt_cond_latent = pickle.loads(gpt_cond_latent_data)
    speaker_embedding = pickle.loads(speaker_embedding_data)

    output = inference(
        voice_cloning_model,
        text, 
        gpt_cond_latent, 
        speaker_embedding
    )

    # local path에 저장
    torchaudio.save(f'{audio_dir_path}{star_id}.wav', output, 24000)

    filename = f'{star_id}.wav'
    local_wav_file_path = f'{audio_dir_path}{filename}'

    # S3 업로드
    object_name = f"star/{star_id}/voice/{filename}"
    s3.upload_audio_file_to_s3(local_wav_file_path, object_name=object_name)
    voice_url = f"https://{s3.S3_BUCKET}.s3.amazonaws.com/{object_name}"

    try:
        if not os.path.exists(local_wav_file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(local_wav_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

    return voice_url
