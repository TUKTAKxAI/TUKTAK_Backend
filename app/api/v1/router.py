from fastapi import APIRouter

from app.api.v1.routes.agreements import router as agreements_router
from app.api.v1.routes.admin_rag import router as admin_rag_router
from app.api.v1.routes.ai_estimates import router as ai_estimates_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.contractor_quotes import detail_router as contractor_quote_detail_router
from app.api.v1.routes.contractor_matching import router as contractor_matching_router
from app.api.v1.routes.contractor_quotes import router as contractor_quotes_router
from app.api.v1.routes.matching_requests import router as matching_requests_router
from app.api.v1.routes.quotes import router as quotes_router
from app.api.v1.routes.work_orders import router as work_orders_router
from app.api.v1.routes.catalog import router as catalog_router
from app.api.v1.routes.contractors import router as contractors_router
from app.api.v1.routes.risk_reports import router as risk_reports_router
from app.api.v1.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(agreements_router)
api_router.include_router(matching_requests_router)
api_router.include_router(quotes_router)
api_router.include_router(contractor_matching_router)
api_router.include_router(contractor_quotes_router)
api_router.include_router(contractor_quote_detail_router)
api_router.include_router(work_orders_router)
api_router.include_router(users_router)
api_router.include_router(catalog_router)
api_router.include_router(risk_reports_router)
api_router.include_router(contractors_router)
api_router.include_router(ai_estimates_router)
api_router.include_router(admin_rag_router)
