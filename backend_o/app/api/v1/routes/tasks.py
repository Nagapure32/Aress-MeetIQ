from fastapi import APIRouter

from app.api.v1.schemas import TaskCreate, TaskItem, TaskUpdate
from app.services.tasks import (
    create_user_task,
    delete_user_task,
    list_user_tasks,
    update_user_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=dict[str, list[TaskItem]])
async def list_tasks() -> dict[str, list]:
    return {"items": await list_user_tasks()}


@router.post("", response_model=TaskItem)
async def create_task(payload: TaskCreate) -> dict:
    return await create_user_task(payload)


@router.put("/{task_id}", response_model=TaskItem)
async def update_task(task_id: str, payload: TaskUpdate) -> dict:
    return await update_user_task(task_id, payload)


@router.delete("/{task_id}")
async def delete_task(task_id: str) -> dict[str, str]:
    await delete_user_task(task_id)
    return {"status": "deleted"}
