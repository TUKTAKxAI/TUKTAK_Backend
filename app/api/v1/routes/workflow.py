from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import (
    ContractorProfile,
    ContractorQuote,
    MatchingRequest,
    MatchingTarget,
    Notification,
    Review,
    User,
    WorkOrder,
)
from app.schemas.common import (
    NotificationListResponse,
    NotificationReadResponse,
    QuoteCreateRequest,
    QuoteCreateResponse,
    QuoteDetailResponse,
    QuoteListResponse,
    ReviewCreateRequest,
    ReviewCreateResponse,
    ReviewDeleteResponse,
    ReviewListResponse,
    ReviewUpdateRequest,
    ReviewUpdateResponse,
    WorkOrderDetailResponse,
)

router = APIRouter(tags=["Quote", "Work Order", "Notification", "Review"])


def _quote_dict(q: ContractorQuote, contractor: ContractorProfile | None = None) -> dict:
    return {
        "quote_id": q.quote_id,
        "matching_request_id": q.matching_request_id,
        "contractor": None if contractor is None else {
            "contractor_id": contractor.contractor_id,
            "business_name": contractor.business_name,
            "rating_avg": contractor.rating_avg,
            "review_count": contractor.review_count,
        },
        "quote_status": q.quote_status,
        "total_amount": q.total_amount,
        "work_scope": q.work_scope,
        "quote_items": q.quote_items_json,
        "included_items": q.included_items_json,
        "excluded_items": q.excluded_items_json,
        "estimated_minutes": q.estimated_minutes,
        "visit_count": q.visit_count,
        "available_date": q.available_date,
        "arrival_time": q.arrival_time,
        "as_period_days": q.as_period_days,
        "valid_until": q.valid_until,
        "additional_note": q.additional_note,
        "sent_at": q.sent_at,
        "selected_at": q.selected_at,
    }


@router.post("/matching-requests/{matching_request_id}/quotes", response_model=QuoteCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    matching_request_id: int,
    payload: QuoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("CONTRACTOR")),
) -> QuoteCreateResponse:
    target_result = await db.execute(
        select(MatchingTarget).where(
            MatchingTarget.matching_request_id == matching_request_id,
            MatchingTarget.contractor_id == current_user.user_id,
        )
    )
    target = target_result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=403, detail="Matching target not assigned to contractor")
    now = datetime.now()
    quote = ContractorQuote(
        matching_request_id=matching_request_id,
        matching_target_id=target.matching_target_id,
        contractor_id=current_user.user_id,
        quote_status="SENT",
        total_amount=payload.total_amount,
        work_scope=payload.work_scope,
        quote_items_json=payload.quote_items,
        included_items_json=payload.included_items,
        excluded_items_json=payload.excluded_items,
        estimated_minutes=payload.estimated_minutes,
        visit_count=payload.visit_count,
        available_date=payload.available_date,
        arrival_time=payload.arrival_time,
        as_period_days=payload.as_period_days,
        valid_until=payload.valid_until,
        additional_note=payload.additional_note,
        sent_at=now,
    )
    target.target_status = "QUOTED"
    target.responded_at = now
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    return QuoteCreateResponse(quote_id=quote.quote_id, quote_status=quote.quote_status, sent_at=quote.sent_at or now)


@router.get("/contractor-quotes/{quote_id}", response_model=QuoteDetailResponse)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuoteDetailResponse:
    quote = await db.get(ContractorQuote, quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    request = await db.get(MatchingRequest, quote.matching_request_id)
    if quote.contractor_id != current_user.user_id and (request is None or request.user_id != current_user.user_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    contractor = await db.get(ContractorProfile, quote.contractor_id)
    return QuoteDetailResponse(quote=_quote_dict(quote, contractor))


@router.get("/contractors/me/quotes", response_model=QuoteListResponse)
async def get_my_quotes(
    quote_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("CONTRACTOR")),
) -> QuoteListResponse:
    query = select(ContractorQuote, MatchingRequest.title, WorkOrder.work_order_id).join(
        MatchingRequest, MatchingRequest.matching_request_id == ContractorQuote.matching_request_id
    ).outerjoin(WorkOrder, WorkOrder.quote_id == ContractorQuote.quote_id).where(
        ContractorQuote.contractor_id == current_user.user_id
    )
    count_query = select(func.count()).select_from(ContractorQuote).where(ContractorQuote.contractor_id == current_user.user_id)
    if quote_status:
        query = query.where(ContractorQuote.quote_status == quote_status)
        count_query = count_query.where(ContractorQuote.quote_status == quote_status)
    rows = (await db.execute(query.order_by(ContractorQuote.sent_at.desc()).offset((page - 1) * size).limit(size))).all()
    total = int((await db.execute(count_query)).scalar_one())
    return QuoteListResponse(
        items=[{
            "quote_id": q.quote_id,
            "matching_request_id": q.matching_request_id,
            "request_title": title,
            "total_amount": q.total_amount,
            "quote_status": q.quote_status,
            "sent_at": q.sent_at,
            "selected_at": q.selected_at,
            "work_order_id": work_order_id,
        } for q, title, work_order_id in rows],
        page=page,
        size=size,
        total=total,
    )


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderDetailResponse)
async def get_work_order(
    work_order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkOrderDetailResponse:
    order = await db.get(WorkOrder, work_order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    if current_user.user_id not in {order.customer_id, order.contractor_id}:
        raise HTTPException(status_code=403, detail="Forbidden")
    customer = await db.get(User, order.customer_id)
    contractor = await db.get(ContractorProfile, order.contractor_id)
    review = (await db.execute(select(Review).where(Review.work_order_id == order.work_order_id, Review.deleted_at.is_(None)))).scalar_one_or_none()
    return WorkOrderDetailResponse(work_order={
        "work_order_id": order.work_order_id,
        "matching_request_id": order.matching_request_id,
        "quote_id": order.quote_id,
        "customer": None if customer is None else {"user_id": customer.user_id, "nickname": customer.nickname, "phone": customer.phone},
        "contractor": None if contractor is None else {"contractor_id": contractor.contractor_id, "business_name": contractor.business_name, "contact_phone": contractor.contact_phone},
        "work_status": order.work_status,
        "scheduled_date": order.scheduled_date,
        "scheduled_start_time": order.scheduled_start_time,
        "scheduled_end_time": order.scheduled_end_time,
        "final_amount": order.final_amount,
        "can_review": current_user.user_id == order.customer_id and order.work_status == "COMPLETED" and review is None,
        "created_at": order.created_at,
    })


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    is_read: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    base = Notification.user_id == current_user.user_id
    query = select(Notification).where(base)
    count_query = select(func.count()).select_from(Notification).where(base)
    if is_read is not None:
        query = query.where(Notification.is_read.is_(is_read))
        count_query = count_query.where(Notification.is_read.is_(is_read))
    unread_count = int((await db.execute(select(func.count()).select_from(Notification).where(base, Notification.is_read.is_(False)))).scalar_one())
    items = (await db.execute(query.order_by(Notification.created_at.desc()).offset((page - 1) * size).limit(size))).scalars().all()
    total = int((await db.execute(count_query)).scalar_one())
    return NotificationListResponse(
        unread_count=unread_count,
        items=[{
            "notification_id": n.notification_id,
            "notification_type": n.notification_type,
            "title": n.title,
            "content": n.content,
            "target_type": n.target_type,
            "target_id": n.target_id,
            "is_read": n.is_read,
            "read_at": n.read_at,
            "created_at": n.created_at,
        } for n in items],
        page=page,
        size=size,
        total=total,
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationReadResponse)
async def read_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadResponse:
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    notification.read_at = datetime.now()
    await db.commit()
    await db.refresh(notification)
    return NotificationReadResponse(notification_id=notification.notification_id, is_read=True, read_at=notification.read_at)


@router.post("/work-orders/{work_order_id}/reviews", response_model=ReviewCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    work_order_id: int,
    payload: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("CUSTOMER")),
) -> ReviewCreateResponse:
    order = await db.get(WorkOrder, work_order_id)
    if order is None or order.customer_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Work order not found")
    exists = (await db.execute(select(Review).where(Review.work_order_id == work_order_id, Review.deleted_at.is_(None)))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Review already exists")
    review = Review(work_order_id=work_order_id, customer_id=current_user.user_id, contractor_id=order.contractor_id, **payload.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    await _recalculate_contractor_rating(db, order.contractor_id)
    return ReviewCreateResponse(review_id=review.review_id, review_status=review.review_status, created_at=review.created_at)


@router.get("/users/me/reviews", response_model=ReviewListResponse)
async def get_my_reviews(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewListResponse:
    query = select(Review, ContractorProfile.business_name).join(ContractorProfile, ContractorProfile.contractor_id == Review.contractor_id).where(
        Review.customer_id == current_user.user_id, Review.deleted_at.is_(None)
    )
    total = int((await db.execute(select(func.count()).select_from(Review).where(Review.customer_id == current_user.user_id, Review.deleted_at.is_(None)))).scalar_one())
    rows = (await db.execute(query.order_by(Review.created_at.desc()).offset((page - 1) * size).limit(size))).all()
    return ReviewListResponse(
        items=[{
            "review_id": r.review_id,
            "work_order_id": r.work_order_id,
            "contractor_id": r.contractor_id,
            "contractor_name": name,
            "rating": r.rating,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        } for r, name in rows],
        page=page,
        size=size,
        total=total,
    )


@router.get("/contractors/{contractor_id}/reviews", response_model=ReviewListResponse)
async def get_contractor_reviews(
    contractor_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ReviewListResponse:
    profile = await db.get(ContractorProfile, contractor_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    query = select(Review, User.nickname).join(User, User.user_id == Review.customer_id).where(
        Review.contractor_id == contractor_id,
        Review.is_visible.is_(True),
        Review.deleted_at.is_(None),
    )
    total = int((await db.execute(select(func.count()).select_from(Review).where(Review.contractor_id == contractor_id, Review.is_visible.is_(True), Review.deleted_at.is_(None)))).scalar_one())
    rows = (await db.execute(query.order_by(Review.created_at.desc()).offset((page - 1) * size).limit(size))).all()
    return ReviewListResponse(
        rating_avg=profile.rating_avg,
        review_count=profile.review_count,
        items=[{
            "review_id": r.review_id,
            "customer_nickname": nickname,
            "rating": r.rating,
            "quality_rating": r.quality_rating,
            "price_rating": r.price_rating,
            "punctuality_rating": r.punctuality_rating,
            "kindness_rating": r.kindness_rating,
            "as_rating": r.as_rating,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        } for r, nickname in rows],
        page=page,
        size=size,
        total=total,
    )


@router.patch("/reviews/{review_id}", response_model=ReviewUpdateResponse)
async def update_review(
    review_id: int,
    payload: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewUpdateResponse:
    review = await db.get(Review, review_id)
    if review is None or review.customer_id != current_user.user_id or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Review not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, key, value)
    await db.commit()
    await db.refresh(review)
    await _recalculate_contractor_rating(db, review.contractor_id)
    return ReviewUpdateResponse(review_id=review.review_id, updated_at=review.updated_at)


@router.delete("/reviews/{review_id}", response_model=ReviewDeleteResponse)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewDeleteResponse:
    review = await db.get(Review, review_id)
    if review is None or review.customer_id != current_user.user_id or review.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_visible = False
    review.deleted_at = datetime.now()
    await db.commit()
    await db.refresh(review)
    await _recalculate_contractor_rating(db, review.contractor_id)
    return ReviewDeleteResponse(review_id=review.review_id, is_visible=False, deleted_at=review.deleted_at)


async def _recalculate_contractor_rating(db: AsyncSession, contractor_id: int) -> None:
    result = await db.execute(
        select(func.avg(Review.rating), func.count()).where(
            Review.contractor_id == contractor_id,
            Review.is_visible.is_(True),
            Review.deleted_at.is_(None),
        )
    )
    avg_rating, count = result.one()
    profile = await db.get(ContractorProfile, contractor_id)
    if profile is not None:
        profile.rating_avg = Decimal(str(round(float(avg_rating or 0), 2)))
        profile.review_count = int(count or 0)
        await db.commit()
