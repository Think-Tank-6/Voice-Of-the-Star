from fastapi import FastAPI

from api import star

app = FastAPI()
app.include_router(star.router)

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}



    