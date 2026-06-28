from fastapi import APIRouter

from app.api.v1.routes.agreements import router as agreements_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.contractors import router as contractors_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(agreements_router)
api_router.include_router(contractors_router)