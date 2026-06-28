import hashlib
import json
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_roles
from app.db.database import get_db
from app.db.models import Attachment, RagDocument, User
from app.schemas.common import (
    IdStatusResponse,
    RagDocumentCreateResponse,
    RagDocumentDetail,
    RagDocumentDetailResponse,
    RagDocumentListItem,
    RagDocumentListResponse,
)

router = APIRouter(prefix="/admin/rag-documents", tags=["Admin RAG"])


def _parse_json(value: str | None) -> dict | None:
    if not value:
        return None
    return json.loads(value)


@router.post("", response_model=RagDocumentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_rag_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form(...),
    source_name: str = Form(...),
    source_url: str | None = Form(None),
    published_date: date | None = Form(None),
    effective_date: date | None = Form(None),
    version: str | None = Form(None),
    metadata_json: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
) -> RagDocumentCreateResponse:
    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()
    attachment = Attachment(
        owner_type="RAG_DOCUMENT",
        owner_id=0,
        file_category="DOCUMENT",
        original_name=file.filename or "document",
        storage_key=f"rag/{content_hash}/{file.filename}",
        file_url=f"/uploads/rag/{content_hash}/{file.filename}",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        uploaded_by=current_user.user_id,
    )
    db.add(attachment)
    await db.flush()
    document = RagDocument(
        title=title,
        document_type=document_type,
        source_name=source_name,
        source_url=source_url,
        published_date=published_date,
        effective_date=effective_date,
        version=version,
        file_attachment_id=attachment.attachment_id,
        content_hash=content_hash,
        document_status="PROCESSING",
        metadata_json=_parse_json(metadata_json),
        created_by=current_user.user_id,
    )
    db.add(document)
    await db.flush()
    attachment.owner_id = document.document_id
    await db.commit()
    await db.refresh(document)
    return RagDocumentCreateResponse(
        document_id=document.document_id,
        document_status=document.document_status,
        created_at=document.created_at,
    )


@router.get("", response_model=RagDocumentListResponse)
async def list_rag_documents(
    document_status: str | None = Query(None),
    document_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
) -> RagDocumentListResponse:
    query = select(RagDocument)
    count_query = select(func.count()).select_from(RagDocument)
    if document_status:
        query = query.where(RagDocument.document_status == document_status)
        count_query = count_query.where(RagDocument.document_status == document_status)
    if document_type:
        query = query.where(RagDocument.document_type == document_type)
        count_query = count_query.where(RagDocument.document_type == document_type)
    query = query.order_by(RagDocument.created_at.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()
    total = int((await db.execute(count_query)).scalar_one())
    return RagDocumentListResponse(
        items=[RagDocumentListItem.model_validate(item) for item in items],
        page=page,
        size=size,
        total=total,
    )


@router.get("/{document_id}", response_model=RagDocumentDetailResponse)
async def get_rag_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
) -> RagDocumentDetailResponse:
    result = await db.execute(select(RagDocument).where(RagDocument.document_id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="RAG document not found")
    file_url = None
    if document.file_attachment_id:
        att = await db.get(Attachment, document.file_attachment_id)
        file_url = att.file_url if att else None
    data = RagDocumentDetail.model_validate(document)
    data.file_url = file_url
    return RagDocumentDetailResponse(document=data)


@router.patch("/{document_id}", response_model=IdStatusResponse)
async def update_rag_document(
    document_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
) -> IdStatusResponse:
    document = await db.get(RagDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="RAG document not found")
    for field in ["title", "document_type", "source_name", "source_url", "published_date", "effective_date", "version", "document_status", "metadata_json"]:
        if field in payload:
            setattr(document, field, payload[field])
    await db.commit()
    await db.refresh(document)
    return IdStatusResponse(document_id=document.document_id, document_status=document.document_status, updated_at=document.updated_at)


@router.delete("/{document_id}", response_model=IdStatusResponse)
async def delete_rag_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
) -> IdStatusResponse:
    document = await db.get(RagDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="RAG document not found")
    document.document_status = "INACTIVE"
    await db.commit()
    await db.refresh(document)
    return IdStatusResponse(document_id=document.document_id, document_status=document.document_status, updated_at=document.updated_at)
