from fastapi import APIRouter

from app.api.v1.schemas import DashboardOverview
from app.services.dashboard import get_dashboard_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOverview)
async def get_dashboard() -> DashboardOverview:
    return await get_dashboard_overview()
