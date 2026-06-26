from fastapi import APIRouter

from app.api.v1.routes.agreements import router as agreements_router
from app.api.v1.routes.auth import router as auth_router
# ai_estimate 라우터 추가
from app.api.v1.routes.ai_estimate import router as ai_estimate_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(agreements_router)
# ai_estimate 라우터 추가
api_router.include_router(ai_estimate_router)