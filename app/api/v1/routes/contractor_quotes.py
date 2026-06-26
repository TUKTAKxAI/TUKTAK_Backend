from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User
from app.schemas.quote import ContractorQuoteListResponse, QuoteDetailResponse
from app.services import quote as quote_service

router = APIRouter(prefix="/contractors/me/quotes", tags=["Contractor Quote"])
detail_router = APIRouter(prefix="/contractor-quotes", tags=["Contractor Quote"])


@router.get("", response_model=ContractorQuoteListResponse)
async def list_contractor_quotes(
    quote_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractorQuoteListResponse:
    items, page, size, total = await quote_service.list_contractor_quotes(
        db, current_user, quote_status, page, size
    )
    return ContractorQuoteListResponse(
        items=items,
        page=page,
        size=size,
        total=total,
    )


@detail_router.get("/{quote_id}", response_model=QuoteDetailResponse)
async def get_quote_detail(
    quote_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailResponse:
    quote = await quote_service.get_quote_detail(db, current_user, quote_id)
    return QuoteDetailResponse(quote=quote)
