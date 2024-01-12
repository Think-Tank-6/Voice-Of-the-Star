import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from database.repository import MessageRepository, GptMessageRepository, UserRepository
from service.auth import HTTPException
import json
import logging
from service.ai_serving import ChatGeneration, DetectCrime
from security import get_access_token
from database.orm import User
from service.auth import AuthService

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

    #p_data 가져오기
    p_data = gpt_message_repo.get_p_data(star_id)

    # 지금까지 저장된 대화 내역 가져오기
    # gpt_message_list = gpt_message_repo.get_gpt_messages(user_id)
    gpt_message_list = []
    # user_message_list = message_repo.get_messages(star_id, len(message_data))
    user_message_list = []
    
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
                gpt_response, gpt_message_list = generate_gpt_response(user_input, p_data, gpt_message_list)
                
                user_message_list.append({"role":"user","content":user_input})
                user_message_list.append({"role":"assistant","content":gpt_response})

                # 클라이언트에게 사용자 메시지와 GPT 응답 전송
                await manager.send_message(message_data, star_id)
                await manager.send_message(gpt_response, star_id)

            except json.JSONDecodeError:
                logger.error("Error decoding message")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for user: {star_id}")
        
        # 메시지 저장 로직: MessageRepository에 사용자 응답 저장
        message_repo.save_message(star_id=star_id, sender="user", content=user_input)

        # 메시지 저장 로직: MessageRepository에 gpt 응답 저장
        message_repo.save_message(star_id=star_id, sender="assistant", content=gpt_response)
        
        # GptMessageRepository에 사용자 응답 저장
        gpt_message_repo.save_gpt_message(star_id=star_id, sender="user", content=user_input)

        # GptMessageRepository에 gpt 응답 저장
        gpt_message_repo.save_gpt_message(star_id=star_id, sender="assistant", content=gpt_response)
        
        manager.disconnect(star_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        await websocket.close(code=1011) 
        
def generate_gpt_response(user_input,p_data, messages):
    # GPT 모델을 사용하여 응답을 생성하는 로직 구현
    chat_generation = ChatGeneration(user_input,p_data, messages)
    gpt_response = chat_generation.get_gpt_answer()
    return gpt_response, messages

def detect_criminal_activity(text_input) -> bool:
    # 함수 밖에 선언 필요 (추후 수정)
    voice_phishing_p_data = ""
    detect_crime = DetectCrime(voice_phishing_p_data)

    is_detected = detect_crime.detect_voice_phishing(text_input)
    return is_detected