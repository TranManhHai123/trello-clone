from pydantic import BaseModel
from typing import Literal
from app.models.task_request import RequestAction, RequestStatus

class TaskRequestResponse(BaseModel):
    id: int
    project_id: int
    task_id: int | None
    task_title: str | None
    requester_id: int
    requester_username: str | None = None 
    action_type: RequestAction
    payload: dict | None 
    status: RequestStatus

    class Config:
        from_attributes = True

class TaskRequestResolve(BaseModel):
    decision: Literal["approved", "rejected"]