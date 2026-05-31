from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import task_service
from app.repositories.user_repository import user_repo

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


@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def get_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tasks = task_service.get_tasks(db, project_id=project_id, user_id=current_user.id)
    return [_build_response(t, db) for t in tasks]


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201)
def create_task(
    project_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = task_service.create(
        db, project_id=project_id, user_id=current_user.id,
        title=data.title, description=data.description, assigned_to=data.assigned_to
    )
    return _build_response(task, db)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
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
    return _build_response(task, db)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task_service.delete(db, task_id=task_id, user_id=current_user.id)