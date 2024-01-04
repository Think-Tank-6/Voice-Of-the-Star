from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import star, user, chat  # 'api' 디렉토리에 있는 모듈을 임포트합니다.

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:19002",
    "http://localhost:19006",
    "http://192.168.0.69:8081",  
    "http://192.168.0.69:19002",  
    "http://192.168.0.69:8000",  
    "ws://192.168.0.119:8081",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(star.router)
app.include_router(user.router)
app.include_router(chat.router)

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}