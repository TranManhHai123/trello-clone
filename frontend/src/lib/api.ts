import axios from 'axios';
import { useAuthStore } from '@/store/authStore';
 
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});
 
// Tự động đính token vào mọi request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data: { email: string; username: string; password: string }) =>
    api.post('/auth/register', data),
 
  login: (data: { email: string; password: string }) => {
    const formData = new URLSearchParams();
    formData.append('username', data.email); // OAuth2 dùng field "username"
    formData.append('password', data.password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
 
  // Lấy thông tin user đang đăng nhập
  me: () => api.get('/auth/me'),
};
 
export const projectAPI = {
  getAll: () => api.get('/projects'),
  create: (data: { name: string; description?: string }) =>
    api.post('/projects', data),
  delete: (id: number) => api.delete(`/projects/${id}`),
};
 
export const taskAPI = {
  getByProject: (projectId: number) =>
    api.get(`/projects/${projectId}/tasks`),
  create: (projectId: number, data: 
    { title: string;
      description?: string;
      assigned_to?: number | null }) =>
    api.post(`/projects/${projectId}/tasks`, data),
  update: (taskId: number, data: { status?: string; title?: string; description?: string; assigned_to?: number | null }) =>
    api.patch(`/tasks/${taskId}`, data),
  delete: (taskId: number) => api.delete(`/tasks/${taskId}`),
};

export interface Member {
  id: number;
  user_id: number;
  role: "owner" | "member";
  user_email: string;
  user_username: string | null;
}

export const memberAPI = {
  getByProject: (projectId: number) =>
    api.get<Member[]>(`/projects/${projectId}/members`),
};

export const taskRequestAPI = {
  getPending: (projectId: number) => api.get(`/projects/${projectId}/requests`),
  resolve: (projectId: number, requestId: number, decision: 'approved' | 'rejected') =>
    api.patch(`/projects/${projectId}/requests/${requestId}`, { decision }),
  cancel: (projectId: number, requestId: number) =>
    api.delete(`/projects/${projectId}/requests/${requestId}`),
};

export default api;