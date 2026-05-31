"use client";
import { useState } from "react";
import { Draggable } from "@hello-pangea/dnd";
import { Trash2, Pencil, Check, X, UserCircle } from "lucide-react";
import { Task, useTaskStore } from "@/store/taskStore";
import { taskAPI, Member } from "@/lib/api";

interface Props {
  task: Task;
  index: number;
  members: Member[];
}

export default function TaskCard({ task, index, members }: Props) {
  const { removeTask, updateTask } = useTaskStore();

  // Edit title state
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(task.title);
  const [saving, setSaving] = useState(false);

  // Assign state
  const [showAssign, setShowAssign] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this task?")) return;
    try {
      await taskAPI.delete(task.id);
      removeTask(task.id);
    } catch {
      alert("Failed to delete task");
    }
  };

  const handleEditStart = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditTitle(task.title);
    setEditing(true);
  };

  const handleSaveTitle = async () => {
    if (!editTitle.trim() || editTitle.trim() === task.title) {
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await taskAPI.update(task.id, { title: editTitle.trim() });
      updateTask(task.id, { title: editTitle.trim() });
      setEditing(false);
    } catch {
      alert("Failed to update task");
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditTitle(task.title);
    setEditing(false);
  };

  const handleAssign = async (
    userId: number | null,
    username: string | null,
  ) => {
    try {
      await taskAPI.update(task.id, { assigned_to: userId });
      updateTask(task.id, { assigned_to: userId, assignee_username: username });
    } catch {
      alert("Failed to assign task");
    }
    setShowAssign(false);
  };

  return (
    <Draggable draggableId={String(task.id)} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`bg-white rounded-lg p-3 shadow-sm border border-gray-200 group
            ${snapshot.isDragging ? "shadow-lg rotate-1 border-blue-300" : "hover:shadow-md"}`}
        >
          {/* Title row */}
          {editing ? (
            // Edit mode: input + Save/Cancel (từ file 18 — UX rõ hơn onBlur)
            <div className="space-y-2" onClick={(e) => e.stopPropagation()}>
              <input
                autoFocus
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveTitle();
                  if (e.key === "Escape") handleCancelEdit();
                }}
                className="w-full border-2 border-blue-400 rounded-md px-2 py-1 text-sm text-gray-900 bg-white focus:outline-none focus:border-blue-500"
              />
              <div className="flex gap-1 justify-end">
                <button
                  onClick={handleSaveTitle}
                  disabled={saving}
                  className="flex items-center gap-1 bg-blue-600 text-white text-xs px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  <Check size={12} /> Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center gap-1 bg-gray-200 text-gray-700 text-xs px-2 py-1 rounded hover:bg-gray-300"
                >
                  <X size={12} /> Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-gray-800 flex-1">
                {task.title}
              </p>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={handleEditStart}
                  className="text-gray-400 hover:text-blue-500"
                >
                  <Pencil size={13} />
                </button>
                <button
                  onClick={handleDelete}
                  className="text-gray-400 hover:text-red-500"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          )}

          {/* Description — ẩn khi đang edit (từ file 18) */}
          {task.description && !editing && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">
              {task.description}
            </p>
          )}

          {/* Assignee badge + dropdown (từ file 19) */}
          {!editing && (
            <div className="mt-2 relative">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowAssign(!showAssign);
                }}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
              >
                <UserCircle size={13} />
                {task.assignee_username
                  ? `@${task.assignee_username}`
                  : "Assign..."}
              </button>

              {showAssign && (
                <div className="absolute z-10 top-6 left-0 bg-white border rounded-lg shadow-lg py-1 min-w-[160px]">
                  <button
                    onClick={() => handleAssign(null, null)}
                    className="w-full text-left px-3 py-1.5 text-xs text-gray-500 hover:bg-gray-50"
                  >
                    — Unassigned —
                  </button>
                  {members.map((m) => (
                    <button
                      key={m.user_id}
                      onClick={() => handleAssign(m.user_id, m.user_username)}
                      className="w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-blue-50"
                    >
                      @{m.user_username}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Draggable>
  );
}
