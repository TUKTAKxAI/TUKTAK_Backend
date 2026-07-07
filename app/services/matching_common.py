from fastapi import HTTPException

from app.db.models import User

CUSTOMER_ROLES = {"CUSTOMER", "BOTH"}
CONTRACTOR_ROLES = {"CONTRACTOR", "BOTH"}


def require_customer(user: User) -> None:
    if user.user_type not in CUSTOMER_ROLES:
        raise HTTPException(status_code=403, detail="Customer account required")


def require_contractor(user: User) -> None:
    if user.user_type not in CONTRACTOR_ROLES:
        raise HTTPException(status_code=403, detail="Contractor account required")


def pagination(page: int, size: int) -> tuple[int, int]:
    return max(page, 1), min(max(size, 1), 100)
