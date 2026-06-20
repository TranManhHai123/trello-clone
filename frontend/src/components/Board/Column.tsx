"use client";
import { useState } from "react";
import { Droppable } from "@hello-pangea/dnd";
import { Plus } from "lucide-react";
import { Task, useTaskStore } from "@/store/taskStore";
import { taskAPI, Member } from "@/lib/api";
import TaskCard from "./TaskCard";

type UserRole = "owner" | "member" | null;

interface Props {
  columnId: string;
  label: string;
  tasks: Task[];
  projectId: number;
  members: Member[];
  currentUserRole: UserRole;
}

export default function Column({
  columnId,
  label,
  tasks,
  projectId,
  members,
  currentUserRole,
}: Props) {
  const isOwner = currentUserRole === "owner";
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState("");
  const [assignedTo, setAssignedTo] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const { addTask } = useTaskStore();

  const handleAddTask = async () => {
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await taskAPI.create(projectId, {
        title: title.trim(),
        // Member không được chọn assignee — BE tự gán cho chính họ.
        // Chỉ owner mới thực sự gửi assigned_to lên.
        assigned_to: isOwner ? assignedTo : null,
      });
      addTask(res.data);
      setTitle("");
      setAssignedTo(null);
      setAdding(false);
    } catch {
      alert("Failed to create task");
    } finally {
      setLoading(false);
    }
  };

  const colorMap: Record<string, string> = {
    todo: "bg-gray-100 border-gray-300",
    in_progress: "bg-yellow-50 border-yellow-300",
    done: "bg-green-50 border-green-300",
  };

  return (
    <div
      className={`flex flex-col rounded-xl border-2 ${colorMap[columnId]} w-72 min-w-[18rem] p-3 self-start`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-700">{label}</h3>
        <span className="text-xs bg-white border rounded-full px-2 py-0.5 text-gray-500">
          {tasks.length}
        </span>
      </div>

      <Droppable droppableId={columnId}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`flex flex-col gap-2 rounded-lg transition-colors
              ${
                snapshot.isDraggingOver
                  ? "bg-blue-50 min-h-[4rem]"
                  : "min-h-[2rem]"
              }`}
          >
            {tasks.map((task, index) => (
              <TaskCard
                key={task.id}
                task={task}
                index={index}
                members={members}
                currentUserRole={currentUserRole}
              />
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>

      {adding ? (
        <div className="mt-2 space-y-2">
          <input
            autoFocus
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAddTask();
              if (e.key === "Escape") setAdding(false);
            }}
            placeholder="Task title..."
            className="w-full border-2 border-blue-400 bg-white text-gray-900 rounded-lg p-2 text-sm placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          />

          {/* Dropdown chọn assignee — chỉ owner thấy. Member tạo task sẽ tự động được gán cho chính mình ở BE. */}
          {isOwner && (
            <select
              value={assignedTo ?? ""}
              onChange={(e) =>
                setAssignedTo(e.target.value ? parseInt(e.target.value) : null)
              }
              className="w-full border border-gray-300 rounded-lg p-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            >
              <option value="">— Unassigned —</option>
              {members.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  @{m.user_username}
                </option>
              ))}
            </select>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleAddTask}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white text-sm py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Add
            </button>
            <button
              onClick={() => {
                setAdding(false);
                setTitle("");
                setAssignedTo(null);
              }}
              className="flex-1 bg-gray-200 text-gray-700 text-sm py-1.5 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="mt-2 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 hover:bg-white rounded-lg p-2 transition-colors"
        >
          <Plus size={16} /> Add Task
        </button>
      )}
    </div>
  );
}
