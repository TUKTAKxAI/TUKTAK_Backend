from fastapi import APIRouter

from app.core.agreements import get_agreement_catalog
from app.schemas.auth import AgreementListResponse, AgreementResponse

router = APIRouter(prefix="/agreements", tags=["Agreement"])


@router.get("/required", response_model=AgreementListResponse)
async def required_agreements() -> AgreementListResponse:
    return AgreementListResponse(
        agreements=[
            AgreementResponse.model_validate(item)
            for item in get_agreement_catalog()
            if item.is_required
        ]
    )
