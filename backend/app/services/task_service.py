from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional, List

from app.repositories.task_repository import task_repo
from app.repositories.project_member_repository import project_member_repo
from app.models.task import Task, TaskStatus


class TaskService:

    def get_task_or_404(self, db: Session, task_id: int, user_id: int) -> Task:
        """Lấy task và kiểm tra membership — dùng chung cho update, delete, và WS broadcast."""
        task = task_repo.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not project_member_repo.is_member(db, task.project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to access this task")
        return task

    def get_tasks(self, db: Session, project_id: int, user_id: int) -> List[Task]:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to view tasks in this project")
        return task_repo.get_by_project(db, project_id)

    def create(self, db: Session, project_id: int, user_id: int,
               title: str, description: str | None = None,
               assigned_to: int | None = None) -> Task:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to add tasks to this project")

        if not project_member_repo.is_owner(db, project_id, user_id):
            assigned_to = user_id

        return task_repo.create(
            db,
            title=title,
            project_id=project_id,
            description=description,
            assigned_to=assigned_to
        )

    def update(self, db: Session, task_id: int, user_id: int,
               title: str | None = None,
               description: str | None = None,
               status: TaskStatus | None = None,
               assigned_to: int | None = None,
               assigned_to_provided: bool = False) -> Task:
        task = self.get_task_or_404(db, task_id, user_id)

        if assigned_to_provided and not project_member_repo.is_owner(db, task.project_id, user_id):
            raise HTTPException(status_code=403, detail="Only project owner can assign tasks")

        return task_repo.update(
            db, task,
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            provided_fields={"assigned_to"} if assigned_to_provided else set(),
        )

    def delete(self, db: Session, task_id: int, user_id: int) -> None:
        task = task_repo.get_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if not project_member_repo.is_owner(db, task.project_id, user_id):
            raise HTTPException(status_code=403, detail="You do not have permission to delete this task")
        task_repo.delete(db, task)


task_service = TaskService()