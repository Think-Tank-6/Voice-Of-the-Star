from fastapi import FastAPI

from api import star, user

app = FastAPI()
app.include_router(star.router)
app.include_router(user.router)

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}