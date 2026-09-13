from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Union
from app.core.security import decode_token
from app.repositories.project_member_repository import project_member_repo

from app.core.database import get_db, SessionLocal
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.task_request import TaskRequest, RequestAction
from app.repositories.user_repository import user_repo
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.schemas.task_request import TaskRequestResponse
from app.services.task_service import task_service
from app.core.websocket_manager import manager

router = APIRouter(tags=["Tasks"])


def _build_task_response(db: Session, task: Task) -> TaskResponse:
    assignee = user_repo.get_by_id(db, task.assigned_to) if task.assigned_to else None
    return TaskResponse(
        id=task.id, title=task.title, description=task.description,
        status=task.status, project_id=task.project_id,
        assigned_to=task.assigned_to,
        assignee_username=assignee.username if assignee else None,
    )


def _build_request_response(db: Session, request: TaskRequest) -> TaskRequestResponse:
    requester = user_repo.get_by_id(db, request.requester_id)

    if request.task_id:
        task_title = task_service.get_title(db, request.task_id)
    else:
        task_title = (request.payload or {}).get("title")

    return TaskRequestResponse(
        id=request.id, project_id=request.project_id, task_id=request.task_id,
        task_title=task_title,
        requester_id=request.requester_id,
        requester_username=requester.username if requester else None,
        action_type=request.action_type, payload=request.payload,
        status=request.status,
    )

@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str | None = Query(default=None),
):
    if not token:
        await websocket.close(code=1008)
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = user_repo.get_by_id(db, int(payload["sub"]))
        if not user:
            await websocket.close(code=1008)
            return

        if not project_member_repo.is_member(db, project_id, user.id):
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)

@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = task_service.get_tasks(db, project_id=project_id, user_id=current_user.id)
    return [_build_task_response(db, t) for t in tasks]


@router.post("/projects/{project_id}/tasks",
             response_model=Union[TaskResponse, TaskRequestResponse])
async def create_task(project_id: int, data: TaskCreate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    result = task_service.create(
        db, project_id=project_id, user_id=current_user.id,
        title=data.title, description=data.description,
        assigned_to=data.assigned_to,
    )

    if isinstance(result, TaskRequest):
        response = _build_request_response(db, result)
        await manager.broadcast(project_id, {
            "type": "REQUEST_CREATED",
            "request": response.model_dump(mode="json"),
        })
        return response

    response = _build_task_response(db, result)
    await manager.broadcast(project_id, {
        "type": "TASK_CREATED",
        "task": response.model_dump(mode="json"),
    })
    return response


@router.patch("/tasks/{task_id}",
              response_model=Union[TaskResponse, TaskRequestResponse])
async def update_task(task_id: int, data: TaskUpdate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    result = task_service.update(
        db, task_id=task_id, user_id=current_user.id,
        title=data.title, description=data.description,
        status=data.status, assigned_to=data.assigned_to,
        assigned_to_provided="assigned_to" in data.model_fields_set,
    )

    project_id = result.project_id  

    if isinstance(result, TaskRequest):
        response = _build_request_response(db, result)
        await manager.broadcast(project_id, {
            "type": "REQUEST_CREATED",
            "request": response.model_dump(mode="json"),
        })
        return response

    response = _build_task_response(db, result)
    await manager.broadcast(project_id, {
        "type": "TASK_UPDATED",
        "task": response.model_dump(mode="json"),
    })
    return response


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    # cần project_id để broadcast — lấy trước khi task có thể bị xoá thật
    task = task_service.get_task_or_404(db, task_id, current_user.id)
    project_id = task.project_id

    result = task_service.delete(db, task_id=task_id, user_id=current_user.id)

    if isinstance(result, TaskRequest):
        response = _build_request_response(db, result)
        await manager.broadcast(project_id, {
            "type": "REQUEST_CREATED",
            "request": response.model_dump(mode="json"),
        })
        return response

    # result is None -> owner đã xoá thật
    await manager.broadcast(project_id, {"type": "TASK_DELETED", "task_id": task_id})
    return {"detail": "Task deleted"}