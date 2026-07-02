from fastapi import APIRouter

from app.api.v1.schemas import ApprovalItem
from app.services.approvals import decide_user_approval, list_user_approvals

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=dict[str, list[ApprovalItem]])
async def list_approvals() -> dict[str, list]:
    return {"items": await list_user_approvals()}


@router.post("/{approval_id}/approve", response_model=ApprovalItem)
async def approve_approval(approval_id: str) -> dict:
    return await decide_user_approval(approval_id, "approve")


@router.post("/{approval_id}/reject", response_model=ApprovalItem)
async def reject_approval(approval_id: str) -> dict:
    return await decide_user_approval(approval_id, "reject")
