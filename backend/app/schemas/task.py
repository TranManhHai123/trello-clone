from pydantic import BaseModel, model_validator
from app.models.task import TaskStatus

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.todo
    assigned_to: int | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    assigned_to: int | None = None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self
    
    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    project_id: int
    assigned_to: int | None
    assignee_username: str | None

    class Config:
        from_attributes = True