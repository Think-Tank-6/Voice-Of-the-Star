import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from database.repository import MessageRepository, GptMessageRepository
from security import get_access_token
import json
import logging

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/chat")

async def get_current_user_id(authorization: str = Header(None)):
    """
    Authorization 헤더에서 사용자 ID를 추출합니다.
    """
    if authorization:
        user_id = get_access_token(authorization)
        return user_id
    else:
        return None

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        del self.active_connections[user_id]

    async def send_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

manager = ConnectionManager()

# Create an instance of ChatRepository
message_repo = MessageRepository()
gpt_message_repo = GptMessageRepository()

@router.get("/{room_id}/messages")
async def get_chat_messages(room_id: int, limit: int = 50):
    """
    특정 채팅방의 최근 채팅 메시지를 가져옵니다.
    :param room_id: 채팅방 ID
    :param limit: 반환할 메시지의 최대 개수
    :return: 채팅 메시지 리스트
    """
    try:
        messages = message_repo.get_messages(room_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching messages")

@router.websocket("/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    logger.debug(f"WebSocket connection opened for room: {room_id}")
    await websocket.accept()

    # 초기 메시지를 기다립니다. 이 메시지는 사용자 ID와 star_id를 포함해야 합니다.
    initial_data = await websocket.receive_text()
    try:
        initial_message = json.loads(initial_data)
        user_id = initial_message.get("user_id")
        star_id = initial_message.get("star_id")  # star_id 추가
        if not user_id or not star_id:
            logger.error("No user_id or star_id provided in initial message")
            await websocket.close()
            return

        await manager.connect(websocket, user_id)

        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # 메시지 형식 검증
                if not all(k in message_data for k in ("content",)):
                    logger.error("Invalid message format")
                    continue

                # 메시지 저장 로직: MessageRepository와 GptMessageRepository 모두에 저장
                message_repo.save_message(
                    room_id=room_id,
                    sender=user_id,
                    content=message_data["content"]
                )

                # GptMessageRepository에 응답 저장
                gpt_message_repo.save_gpt_message(
                    star_id=star_id,
                    sender="assistant",  # GPT로부터의 응답을 표시
                    content=gpt_response
                )
                
                # GPT 모델을 사용하여 응답 생성
                gpt_response = generate_gpt_response(message_data["content"])

                # 메시지와 GPT 응답에 room_id와 created_at를 추가합니다.
                message_data['room_id'] = room_id
                message_data['created_at'] = datetime.datetime.utcnow().isoformat()
                gpt_message = {
                    "room_id": room_id,
                    "sender": "GPT",
                    "content": gpt_response,
                    "created_at": datetime.datetime.utcnow().isoformat()
                }

                # 클라이언트에게 사용자 메시지와 GPT 응답을 전송합니다.
                await manager.send_message(message_data, user_id)
                await manager.send_message(gpt_message, user_id)

            except json.JSONDecodeError:
                logger.error("Error decoding message")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for user: {user_id}")
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error: {e}")

def generate_gpt_response(user_input):
    # GPT 모델을 사용하여 응답을 생성하는 로직 구현
    pass
