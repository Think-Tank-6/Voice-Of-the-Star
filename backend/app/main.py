from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from api import star, user, chat, admin  # 'api' 디렉토리에 있는 모듈을 임포트합니다.

app = FastAPI()

load_dotenv()
origins = os.getenv("ORIGIN")

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
app.include_router(admin.router)

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}