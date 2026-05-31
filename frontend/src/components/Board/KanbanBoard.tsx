"use client";
import { DragDropContext, DropResult } from "@hello-pangea/dnd";
import { useTaskStore, Task } from "@/store/taskStore";
import { taskAPI, Member } from "@/lib/api";
import Column from "./Column";

const COLUMNS = [
  { id: "todo", label: "📋 To Do" },
  { id: "in_progress", label: "⚡ In Progress" },
  { id: "done", label: "✅ Done" },
];

interface Props {
  projectId: number;
  members: Member[];
}

export default function KanbanBoard({ projectId, members }: Props) {
  const { tasks, updateTaskStatus } = useTaskStore();

  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId) return;

    const taskId = parseInt(draggableId);
    const newStatus = destination.droppableId as Task["status"];
    const oldStatus = source.droppableId as Task["status"];

    // Optimistic update — cập nhật UI ngay, không cần chờ API
    updateTaskStatus(taskId, newStatus);

    try {
      await taskAPI.update(taskId, { status: newStatus });
    } catch {
      // Revert nếu API lỗi
      updateTaskStatus(taskId, oldStatus);
      alert("Failed to update task, please try again");
    }
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex gap-5 p-6 overflow-x-auto min-h-[calc(100vh-4rem)]">
        {COLUMNS.map((col) => (
          <Column
            key={col.id}
            columnId={col.id}
            label={col.label}
            tasks={tasks.filter((t) => t.status === col.id)}
            projectId={projectId}
            members={members}
          />
        ))}
      </div>
    </DragDropContext>
  );
}
