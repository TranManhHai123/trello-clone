from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus
from typing import List

class TaskRepository:
    def get_by_project(self, db: Session, project_id: int) -> List[Task]:
        return db.query(Task).filter(Task.project_id == project_id).all()

    def get_by_id(self, db: Session, task_id: int) -> Task | None:
        return db.query(Task).filter(Task.id == task_id).first()

    def create(self, db: Session, title: str, project_id: int,
               description: str | None = None,
               status: TaskStatus = TaskStatus.todo,
               assigned_to: int | None = None) -> Task:
        task = Task(title=title, project_id=project_id,
                    description=description, status=status, assigned_to=assigned_to)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update(self, db: Session, task: Task, *,
               provided_fields: set[str] | None = None, **kwargs) -> Task:
        provided_fields = provided_fields or set()
        for key, value in kwargs.items():
            if value is not None or key in provided_fields:
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task: Task):
        db.delete(task)
        db.commit()

task_repo = TaskRepository()