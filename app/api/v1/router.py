from fastapi import APIRouter

from app.api.v1.routes.agreements import router as agreements_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.contractor_quotes import detail_router as contractor_quote_detail_router
from app.api.v1.routes.contractor_matching import router as contractor_matching_router
from app.api.v1.routes.contractor_quotes import router as contractor_quotes_router
from app.api.v1.routes.matching_requests import router as matching_requests_router
from app.api.v1.routes.quotes import router as quotes_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(agreements_router)
api_router.include_router(matching_requests_router)
api_router.include_router(quotes_router)
api_router.include_router(contractor_matching_router)
api_router.include_router(contractor_quotes_router)
api_router.include_router(contractor_quote_detail_router)
