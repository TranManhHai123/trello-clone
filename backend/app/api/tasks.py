from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import task_service
from app.repositories.user_repository import user_repo
from app.core.websocket_manager import manager

router = APIRouter(tags=["Tasks"])


def _build_response(task, db: Session) -> TaskResponse:
    assignee_username = None
    if task.assigned_to:
        assignee = user_repo.get_by_id(db, task.assigned_to)
        assignee_username = assignee.username if assignee else None
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assignee_username=assignee_username,
    )


# ── WebSocket endpoint ──────────────────────────────────────────────────────

@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int):
    """
    Client kết nối vào đây để nhận real-time update của project.
    Không cần auth token ở bước này vì WS handshake không tiện gửi header —
    token có thể truyền qua query param nếu muốn bảo mật thêm sau.
    """
    await manager.connect(websocket, project_id)
    try:
        while True:
            # Giữ kết nối sống — chờ message từ client (ping/pong hoặc ignore)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)


# ── HTTP endpoints ──────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tasks = task_service.get_tasks(db, project_id=project_id, user_id=current_user.id)
    return [_build_response(t, db) for t in tasks]


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = task_service.create(
        db, project_id=project_id, user_id=current_user.id,
        title=data.title, description=data.description, assigned_to=data.assigned_to
    )
    response = _build_response(task, db)

    # Báo cho tất cả client trong project biết có task mới
    await manager.broadcast(project_id, {
        "type": "TASK_CREATED",
        "task": response.model_dump(),
    })

    return response


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = task_service.update(
        db, task_id=task_id, user_id=current_user.id,
        title=data.title, description=data.description,
        status=data.status, assigned_to=data.assigned_to
    )
    response = _build_response(task, db)

    # Broadcast cập nhật — client dùng task.id để tìm và update đúng task
    await manager.broadcast(task.project_id, {
        "type": "TASK_UPDATED",
        "task": response.model_dump(),
    })

    return response


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Lấy project_id trước khi xóa (sau khi xóa không còn object nữa)
    task = task_service.get_task_or_404(db, task_id=task_id, user_id=current_user.id)
    project_id = task.project_id

    task_service.delete(db, task_id=task_id, user_id=current_user.id)

    # Báo cho client xóa task khỏi UI
    await manager.broadcast(project_id, {
        "type": "TASK_DELETED",
        "task_id": task_id,
    })