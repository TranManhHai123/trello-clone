import { create } from "zustand";

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: "todo" | "in_progress" | "done";
  project_id: number;
  assigned_to: number | null;
  assignee_username: string | null;
}

interface TaskStore {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  updateTaskStatus: (taskId: number, status: Task["status"]) => void;
  addTask: (task: Task) => void;
  removeTask: (taskId: number) => void;
  updateTask: (taskId: number, data: Partial<Task>) => void;
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
  // Idempotent: nếu task đã tồn tại (vd HTTP response add trước, rồi WS broadcast
  // TASK_CREATED của chính mình đến sau) → update thay vì thêm trùng, tránh duplicate key.
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
}));