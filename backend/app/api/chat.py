from fastapi import APIRouter, WebSocket
from database.connection import get_messages_collection 
import json
import logging

# 로거 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

router = APIRouter(prefix="/chat")

# 연결된 클라이언트를 관리하기 위한 딕셔너리입니다.
connected_clients = {}

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    logger.debug(f"WebSocket connection opened for client: {client_id}")
    await websocket.accept()
    connected_clients[client_id] = websocket
    # MongoDB의 메시지 컬렉션 가져오기
    messages_collection = get_messages_collection()
    try:
        while True:
            # 클라이언트로부터 메시지를 기다립니다.
            data = await websocket.receive_text()
            message = json.loads(data)

             # MongoDB에 메시지 저장
            try:
                messages_collection.insert_one(message)
            except Exception as e:
                logger.error(f"Failed to insert message into MongoDB: {e}")
            
            # 모든 클라이언트에게 메시지를 전송합니다.
            for client in connected_clients.values():
                await client.send_text(json.dumps(message))
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # 클라이언트 연결이 끊어지면 리스트에서 제거합니다.
        del connected_clients[client_id]
