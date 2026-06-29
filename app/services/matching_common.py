from fastapi import HTTPException

from app.db.models import User


def require_customer(user: User) -> None:
    if user.user_type != "CUSTOMER":
        raise HTTPException(status_code=403, detail="Customer account required")


def require_contractor(user: User) -> None:
    if user.user_type != "CONTRACTOR":
        raise HTTPException(status_code=403, detail="Contractor account required")


def pagination(page: int, size: int) -> tuple[int, int]:
    return max(page, 1), min(max(size, 1), 100)
