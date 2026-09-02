from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.task_request import RequestAction
from app.repositories.user_repository import user_repo
from app.schemas.task_request import TaskRequestResponse, TaskRequestResolve
from app.services.task_request_service import task_request_service
from app.core.websocket_manager import manager
from app.services import task_service

router = APIRouter(prefix="/projects/{project_id}/requests", tags=["Task Requests"])


def _build_response(db: Session, request) -> TaskRequestResponse:
    requester = user_repo.get_by_id(db, request.requester_id)

    if request.task_id:
        task_title = task_service.get_title(db, request.task_id)
    else:
        task_title = (request.payload or {}).get("title")
    
    return TaskRequestResponse(
        id=request.id,
        project_id=request.project_id,
        task_id=request.task_id,
        task_title=task_title,
        requester_id=request.requester_id,
        requester_username=requester.username if requester else None,
        action_type=request.action_type,
        payload=request.payload,
        status=request.status,
    )


@router.get("", response_model=List[TaskRequestResponse])
def get_requests(project_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    requests = task_request_service.get_pending(db, project_id, current_user.id)
    return [_build_response(db, r) for r in requests]


@router.patch("/{request_id}", response_model=TaskRequestResponse)
async def resolve_request(project_id: int, request_id: int, data: TaskRequestResolve,
                           db: Session = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    request, task = task_request_service.resolve(
        db, project_id, request_id, current_user.id, data.decision
    )

    await manager.broadcast(project_id, {
        "type": "REQUEST_RESOLVED",
        "request_id": request.id,
        "status": request.status.value,
        "task_id": request.task_id,
    })

    if data.decision == "approved":
        if request.action_type == RequestAction.create and task:
            await manager.broadcast(project_id, {
                "type": "TASK_CREATED",
                "task": {
                    "id": task.id, "title": task.title, "description": task.description,
                    "status": task.status.value, "project_id": task.project_id,
                    "assigned_to": task.assigned_to,
                },
            })
        elif request.action_type == RequestAction.update and task:
            await manager.broadcast(project_id, {
                "type": "TASK_UPDATED",
                "task": {
                    "id": task.id, "title": task.title, "description": task.description,
                    "status": task.status.value, "assigned_to": task.assigned_to,
                },
            })
        elif request.action_type == RequestAction.delete:
            await manager.broadcast(project_id, {
                "type": "TASK_DELETED", "task_id": request.task_id,
            })

    return _build_response(db, request)

@router.delete("/{request_id}")
async def cancel_request(project_id: int, request_id: int,
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    info = task_request_service.cancel(db, project_id, request_id, current_user.id)

    await manager.broadcast(project_id, {
        "type": "REQUEST_CANCELLED",
        "request_id": info["id"],
        "task_id": info["task_id"],
    })

    return {"detail": "Request cancelled", "request_id": info["id"]}