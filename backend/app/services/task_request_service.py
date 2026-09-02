from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Tuple

from app.repositories.task_request_repository import task_request_repo
from app.repositories.project_member_repository import project_member_repo
from app.models.task_request import TaskRequest, RequestStatus, RequestAction
from app.models.task import Task, TaskStatus
from app.services.task_service import task_service


class TaskRequestService:

    def get_pending(self, db: Session, project_id: int, user_id: int) -> List[TaskRequest]:
        if not project_member_repo.is_member(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="Only project member can view requests")
        return task_request_repo.get_pending_by_project(db, project_id)

    def resolve(self, db: Session, project_id: int, request_id: int,
                user_id: int, decision: str) -> Tuple[TaskRequest, Task | None]:
        if not project_member_repo.is_owner(db, project_id, user_id):
            raise HTTPException(status_code=403, detail="Only project owner can resolve requests")

        request = task_request_repo.get_by_id(db, request_id)
        if not request or request.project_id != project_id:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.status != RequestStatus.pending:
            raise HTTPException(status_code=400, detail="Request already resolved")

        task: Task | None = None
        if decision == "approved":
            task = self._execute(db, user_id, request)

        new_status = RequestStatus.approved if decision == "approved" else RequestStatus.rejected
        request = task_request_repo.update_status(db, request, new_status)
        return request, task

    def _execute(self, db: Session, owner_id: int, request: TaskRequest) -> Task | None:
        payload = request.payload or {}

        if request.action_type == RequestAction.create:
            return task_service.create_internal(
                db,
                project_id=request.project_id,
                title=payload.get("title"),
                description=payload.get("description"),
                assigned_to=payload.get("assigned_to"),
            )
        
        task = task_service.get_task_or_404(db, request.task_id, owner_id)

        if request.action_type == RequestAction.update:
            status_val = TaskStatus(payload["status"]) if "status" in payload else None
            return task_service.update_internal(
                db, task,
                title=payload.get("title"),
                description=payload.get("description"),
                status=status_val,
                provided_fields=set(payload.keys()),
            )

        if request.action_type == RequestAction.delete:
            task_service.delete_internal(db, task)
            return None

        return None

    def cancel(self, db: Session, project_id: int, request_id: int, user_id: int) -> dict:
        request = task_request_repo.get_by_id(db, request_id)
        if not request or request.project_id != project_id:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.requester_id != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own request")
        if request.status != RequestStatus.pending:
            raise HTTPException(status_code=400, detail="Request already resolved, cannot cancel")

        info = {
            "id": request.id,
            "task_id": request.task_id,
            "action_type": request.action_type,
        }
        task_request_repo.delete(db, request)
        return info


task_request_service = TaskRequestService()