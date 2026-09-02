import { create } from "zustand";

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "done";
  project_id: number;
  assigned_to: number | null;
  assignee_username: string | null;
  pending_request_id?: number | null;
  pending_action?: 'update' | 'delete' | null;
  pending_old_status?: 'todo' | 'in_progress' | 'done' | null;
  pending_requester_id?: number | null;
}

interface TaskStore {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  updateTaskStatus: (taskId: number, status: Task["status"]) => void;
  addTask: (task: Task) => void;
  removeTask: (taskId: number) => void;
  updateTask: (taskId: number, data: Partial<Task>) => void;
  markTaskPending: (taskId: number, requestId: number, action: 'update' | 'delete', oldStatus?: Task['status'], requesterId?: number) => void;
  clearPending: (taskId: number) => void;
  revertPendingUpdate: (taskId: number) => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, status } : t)),
    })),
  updateTask: (taskId, data) =>
    set((state) => ({
      tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, ...data } : t)),
    })),
  addTask: (task) =>
    set((state) => {
      const exists = state.tasks.some((t) => t.id === task.id);
      if (exists) {
        return {
          tasks: state.tasks.map((t) => (t.id === task.id ? task : t)),
        };
      }
      return { tasks: [...state.tasks, task] };
    }),
  removeTask: (taskId) =>
    set((state) => ({ tasks: state.tasks.filter((t) => t.id !== taskId) })),
  markTaskPending: (taskId, requestId, action, oldStatus, requesterId) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId
          ? { ...t, pending_request_id: requestId, pending_action: action, pending_old_status: oldStatus ?? null, pending_requester_id: requesterId ?? null }
          : t
      ),
    })),

  clearPending: (taskId) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId
          ? { ...t, pending_request_id: null, pending_action: null, pending_old_status: null }
          : t
      ),
    })),

  revertPendingUpdate: (taskId) =>
  set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === taskId
        ? {
            ...t,
            ...(t.pending_old_status ? { status: t.pending_old_status } : {}),
            pending_request_id: null,
            pending_action: null,
            pending_old_status: null,
          }
        : t
    ),
  })),
  }));