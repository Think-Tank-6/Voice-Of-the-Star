import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        del self.active_connections[client_id]

    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))

manager = ConnectionManager()

# Create an instance of ChatRepository
chat_repo = ChatRepository()

@router.websocket("/{client_id}/{room_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, room_id: int):
    logger.debug(f"WebSocket connection opened for client: {client_id} in room: {room_id}")
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                # 메시지 형식 검증: 필요한 키들이 있는지 확인
                if not all(k in message_data for k in ("user_id", "star_id", "message")):
                    logger.error("Invalid message format")
                    continue

                # repository 모듈의 save_message 함수를 사용하여 메시지를 MongoDB에 저장합니다.
                chat_repo.save_message(
                    room_id=room_id,
                    user_id=message_data["user_id"],
                    star_id=message_data["star_id"],
                    message_text=message_data["message"]
                )

                # 메시지에 room_id와 created_at를 추가합니다.
                message_data['room_id'] = room_id
                message_data['created_at'] = datetime.datetime.utcnow().isoformat()

                # 해당 클라이언트에게 메시지를 전송합니다.
                await manager.send_message(message_data, client_id)
            except json.JSONDecodeError:
                logger.error("Error decoding message")
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for client: {client_id}")
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Error: {e}")
