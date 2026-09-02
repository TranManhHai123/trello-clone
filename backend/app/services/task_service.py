from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List

from app.repositories.task_repository import task_repo
from app.repositories.project_member_repository import project_member_repo
from app.repositories.task_request_repository import task_request_repo
from app.models.task import Task, TaskStatus
from app.models.task_request import TaskRequest, RequestStatus, RequestAction


class TaskService:

    def get_task_or_404(self, db: Session, task_id: int, user_id: int) -> Task:
        task = task_repo.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not project_member_repo.is_member(db, task.project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to access this task")
        return task

    def get_title(self, db: Session, task_id: int) -> str | None:
        task = task_repo.get_by_id(db, task_id)
        return task.title if task else None

    def get_tasks(self, db: Session, project_id: int, user_id: int) -> List[Task]:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to view tasks in this project")
        return task_repo.get_by_project(db, project_id)

    def create_internal(self, db: Session, project_id: int, title: str,
                          description: Optional[str] = None,
                          status: TaskStatus = TaskStatus.todo,
                          assigned_to: Optional[int] = None) -> Task:
    
        return task_repo.create(
            db, title=title, project_id=project_id,
            description=description, status=status, assigned_to=assigned_to
    )

    def create(self, db: Session, project_id: int, user_id: int,
               title: str, description: str | None = None,
               assigned_to: int | None = None) -> Task | TaskRequest:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to add tasks to this project")

        is_owner = project_member_repo.is_owner(db, project_id, user_id)

        if is_owner:
            return self.create_internal(
                db, project_id, title,
                description=description,
                assigned_to=assigned_to,
        )

        

        payload = {"title": title, "description": description, "assigned_to": user_id}
        return task_request_repo.create(
            db, project_id=project_id, requester_id=user_id,
            action_type=RequestAction.create, payload=payload
        )

    def update_internal(self, db: Session, task: Task,
                     title: str | None = None,
                     description: str | None = None,
                     status: TaskStatus | None = None,
                     assigned_to: int | None = None,
                     provided_fields: set = set()) -> Task:
        return task_repo.update(
            db, task,
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            provided_fields=provided_fields,
    )

    def update(self, db: Session, task_id: int, user_id: int,
               title: str | None = None,
               description: str | None = None,
               status: TaskStatus | None = None,
               assigned_to: int | None = None,
               assigned_to_provided: bool = False) -> Task | TaskRequest:
        task = self.get_task_or_404(db, task_id, user_id)

        is_owner = project_member_repo.is_owner(db, task.project_id, user_id)

        if assigned_to_provided and not is_owner:
            raise HTTPException(status_code=403, detail="Only project owner can assign tasks")

        if is_owner:
            return self.update_internal(
                db, task,
                title=title,
                description=description,
                status=status,
                assigned_to=assigned_to,
                provided_fields={"assigned_to"} if assigned_to_provided else set(),
            )

        if task_request_repo.get_pending_by_task(db, task.id):
            raise HTTPException(
                status_code=409,
                detail="This task already has a pending request. Please wait for owner's decision."
            )
        
        payload = {}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status.value

        return task_request_repo.create(
            db,
            project_id=task.project_id,
            requester_id=user_id,
            action_type=RequestAction.update,
            payload=payload,
            task_id=task.id,
    )

    def delete_internal(self, db: Session, task: Task) -> None:
        task_repo.delete(db, task)

    def delete(self, db: Session, task_id: int, user_id: int) -> TaskRequest | None:
        task = self.get_task_or_404(db, task_id, user_id)
        
        if project_member_repo.is_owner(db, task.project_id, user_id):
            self.delete_internal(db, task)
            return None

        if task_request_repo.get_pending_by_task(db, task.id):
            raise HTTPException(
                status_code=409,
                detail="This task already has a pending request. Please wait for owner's decision."
            )
        
        return task_request_repo.create(
            db,
            project_id=task.project_id,
            requester_id=user_id,
            action_type=RequestAction.delete,
            payload={},
            task_id=task.id,
        )


task_service = TaskService()