from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.quote import (
    QuoteCreate,
    QuoteCreateResponse,
    QuoteListResponse,
    SelectQuoteRequest,
    SelectQuoteResponse,
)
from app.services import quote as quote_service

router = APIRouter(prefix="/matching-requests/{matching_request_id}", tags=["Quote"])


@router.post("/quotes", response_model=QuoteCreateResponse, status_code=201)
async def create_matching_request_quote(
    matching_request_id: int,
    payload: QuoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuoteCreateResponse:
    quote = await quote_service.create_quote(db, current_user, matching_request_id, payload)
    return QuoteCreateResponse(
        quote_id=quote.quote_id,
        matching_request_id=quote.matching_request_id,
        contractor_id=quote.contractor_id,
        quote_status=quote.quote_status,
        total_amount=quote.total_amount,
        sent_at=quote.sent_at,
        created_at=quote.created_at,
    )


@router.get("/quotes", response_model=QuoteListResponse)
async def list_matching_request_quotes(
    matching_request_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuoteListResponse:
    quotes, page, size, total = await quote_service.list_quotes_for_matching_request(
        db, current_user, matching_request_id, page, size
    )
    return QuoteListResponse(quotes=quotes, page=page, size=size, total=total)


@router.post("/select-quote", response_model=SelectQuoteResponse)
async def select_matching_request_quote(
    matching_request_id: int,
    payload: SelectQuoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SelectQuoteResponse:
    request, quote, work_order = await quote_service.select_quote(
        db, current_user, matching_request_id, payload.quote_id
    )
    return SelectQuoteResponse(
        matching_request_id=request.matching_request_id,
        selected_quote_id=quote.quote_id,
        selected_contractor_id=quote.contractor_id,
        matching_status=request.matching_status,
        work_order_id=work_order.work_order_id,
        created_at=work_order.created_at,
    )
