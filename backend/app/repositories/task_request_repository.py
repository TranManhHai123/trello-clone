# repositories/task_request_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.task_request import TaskRequest, RequestStatus, RequestAction

class TaskRequestRepository:
    def create(self, db: Session, project_id: int, requester_id: int,
               action_type: RequestAction, payload: dict,
               task_id: int | None = None) -> TaskRequest:
        req = TaskRequest(
            project_id=project_id,
            requester_id=requester_id,
            task_id=task_id,
            action_type=action_type,
            payload=payload,
            status=RequestStatus.pending,
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    def get_by_id(self, db: Session, request_id: int) -> Optional[TaskRequest]:
        return db.query(TaskRequest).filter(TaskRequest.id == request_id).first()

    def get_pending_by_project(self, db: Session, project_id: int) -> List[TaskRequest]:
        return db.query(TaskRequest).filter(
            TaskRequest.project_id == project_id,
            TaskRequest.status == RequestStatus.pending
        ).all()

    def get_pending_by_task(self, db: Session, task_id: int) -> Optional[TaskRequest]:
        return db.query(TaskRequest).filter(
            TaskRequest.task_id == task_id,
            TaskRequest.status == RequestStatus.pending
        ).first()

    def get_pending_by_requester(self, db: Session, project_id: int, requester_id: int) -> Optional[TaskRequest]:
        return db.query(TaskRequest).filter(
            TaskRequest.project_id == project_id,
            TaskRequest.requester_id == requester_id,
            TaskRequest.status == RequestStatus.pending
        ).first()

    def update_status(self, db: Session, request: TaskRequest, status: RequestStatus) -> TaskRequest:
        request.status = status
        db.commit()
        db.refresh(request)
        return request

    def delete(self, db: Session, request: TaskRequest) -> None:
        db.delete(request)
        db.commit()
        
task_request_repo = TaskRequestRepository()