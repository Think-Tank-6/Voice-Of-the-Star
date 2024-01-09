import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from database.repository import ChatRepository
import json
import logging

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/chat")

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
chat_repo = ChatRepository()

@router.get("/{room_id}/messages")
async def get_chat_messages(room_id: int, limit: int = 50):
    """
    특정 채팅방의 최근 채팅 메시지를 가져옵니다.
    :param room_id: 채팅방 ID
    :param limit: 반환할 메시지의 최대 개수
    :return: 채팅 메시지 리스트
    """
    try:
        messages = chat_repo.get_messages(room_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages for room {room_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching messages")

@router.websocket("/{user_id}/{room_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, room_id: int):
    logger.debug(f"WebSocket connection opened for user: {user_id} in room: {room_id}")
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # 메시지 형식 검증: 필요한 키들이 있는지 확인
                if not all(k in message_data for k in ("user_id", "star_id", "content")):
                    logger.error("Invalid message format")
                    continue

                # repository 모듈의 save_message 함수를 사용하여 메시지를 MongoDB에 저장합니다.
                chat_repo.save_message(
                    room_id=room_id,
                    user_id=message_data["user_id"],
                    star_id=message_data["star_id"],
                    content=message_data["content"]
                )

                # 메시지에 room_id와 created_at를 추가합니다.
                message_data['room_id'] = room_id
                message_data['created_at'] = datetime.datetime.utcnow().isoformat()

                # 해당 클라이언트에게 메시지를 전송합니다.
                await manager.send_message(message_data, user_id)
            except json.JSONDecodeError:
                logger.error("Error decoding message")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for user: {user_id}")
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error: {e}")
