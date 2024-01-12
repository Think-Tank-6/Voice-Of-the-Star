from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
import numpy as np
import torch
import torchaudio
from ai_models.voice_cloning.xtts import inference
from schema.request import PlayVoiceRequest
from database.repository import MessageRepository, GptMessageRepository, StarRepository, UserRepository
from service.auth import HTTPException, AuthService
import json
import logging
from service.ai_serving import voice_cloning_model, ChatGeneration, DetectCrime
from security import get_access_token
from database.orm import Star, User

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/chat")

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

    def disconnect(self, star_id: str):
        del self.active_connections[star_id]

    async def send_message(self, message: dict, star_id: str):
        if star_id in self.active_connections:
            await self.active_connections[star_id].send_text(json.dumps(message))

manager = ConnectionManager()
message_repo = MessageRepository()
gpt_message_repo = GptMessageRepository()
# user_repo = UserRepository()
# user = Depends(get_authenticated_user)

@router.websocket("/{star_id}")
async def websocket_endpoint(
        websocket: WebSocket, 
        star_id: int
    ):

    
    #p_data 가져오기 (수정필요)
    p_data = gpt_message_repo.get_p_data(star_id)
    if p_data is not None:
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

                # GPT 모델을 사용하여 응답 생성
                # gpt 내에서 자동으로 user_input, gpt_response 저장
                gpt_response, _ = chat_generation.get_gpt_answer(user_input)
                full_message_list.append({"user_input": user_input,"gpt_response":gpt_response})

                # 클라이언트에게 사용자 메시지와 GPT 응답 전송
                await manager.send_message(message_data, star_id)
                await manager.send_message(gpt_response, star_id)

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
        

def detect_criminal_activity(text_input) -> bool:
    # 함수 밖에 선언 필요 (추후 수정)
    voice_phishing_p_data = ""
    detect_crime = DetectCrime(voice_phishing_p_data)

    is_detected = detect_crime.detect_voice_phishing(text_input)
    return is_detected


# Voice Cloning
@router.post("/play-voice/{star_id}", status_code=200)
async def play_voice_handler(
    star_id: int,
    request: PlayVoiceRequest,
    user: User = Depends(get_authenticated_user),
    star_repo: StarRepository = Depends(),
):
    text = request.text

    star: Star | None = star_repo.get_star_by_star_id(star_id=star_id, user_id=user.user_id)

    if not star:
        raise HTTPException(status_code=404, detail="Star Not Found")
    
    # Star 데이터베이스의 gpt_cond_latent, speaker_embedding (.npy 파일) 조회
    gpt_cond_latent_data = star.gpt_cond_latent_data
    speaker_embedding_data = star.speaker_embedding_data
    print("gpt_cond_latent_data : ", type(gpt_cond_latent_data))
    print("speaker_embedding_data : ", type(speaker_embedding_data))

    # numpy 배열로 변환
    gpt_cond_latent_data = np.frombuffer(gpt_cond_latent_data, dtype=np.float32)
    speaker_embedding_data = np.frombuffer(speaker_embedding_data, dtype=np.float32)
    # print("gpt_cond_latent_data.shape() : ", gpt_cond_latent_data.shape())
    # print("speaker_embedding_data.shape() : ", gpt_cond_latent_data.shape())

    # PyTorch tensor 생성 
    gpt_cond_latent = torch.Tensor(gpt_cond_latent_data)
    speaker_embedding = torch.Tensor(speaker_embedding_data)

    print("gpt_cond_latent : ", type(gpt_cond_latent))
    print("speaker_embedding : ", type(speaker_embedding))
    print("2----------------gpt_cond_latent.shape : ", gpt_cond_latent.shape)
    print("2----------------speaker_embedding.shape : ", speaker_embedding.shape)

    output = inference(
        voice_cloning_model,
        text, 
        gpt_cond_latent, 
        speaker_embedding
    )
    print("out : ", output)

    # gpt_cond_latent_data = np.load(gpt_cond_latent_data, allow_pickle=True)
    # gpt_cond_latent_data = np.load(speaker_embedding_data, allow_pickle=True)

    # if isinstance(gpt_cond_latent_data, bytes):
    # gpt_cond_latent_data = np.frombuffer(gpt_cond_latent_data, dtype=np.float32)

    # gpt_cond_latent_npy = np.load(gpt_cond_latent_data)
    # speaker_embedding_npy = np.load(speaker_embedding_data)
    # gpt_cond_latent = torch.from_numpy(gpt_cond_latent_data)
    # speaker_embedding = torch.from_numpy(speaker_embedding_data)



    # if gpt_cond_latent_data == None and speaker_embedding_data == None:
        
    # np.save("gpt_cond_latent.npy", gpt_cond_latent_npy)
    # np.save("speaker_embedding.npy", speaker_embedding_npy)

    # star: Star = star.insert_npy(
    #     gpt_cond_latent_npy=gpt_cond_latent_npy, 
    #     speaker_embedding_npy=speaker_embedding_npy
    # )
    
    # DB save
    # star: Star = star_repo.update_star(star=star)

    # output = inference(AppConfig.model, text, gpt_cond_latent, speaker_embedding)
    # print("out : ", output)

    # 오디오 생성
    output_np = output.numpy()
    file_path = f"./resources/audio/output_{star_id}.wav"
    torchaudio.save(file_path, torch.Tensor(output_np), 24000)

    # return output
    return []