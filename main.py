from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get():
    return "안녕하세요 TukTak 프로젝트의 Backend 개발 환경입니다."