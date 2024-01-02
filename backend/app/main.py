from fastapi import FastAPI

from api import star, auth

app = FastAPI()
app.include_router(star.router)
app.include_router(auth.router)

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}