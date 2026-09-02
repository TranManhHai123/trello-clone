import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  setToken: (token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: typeof window !== 'undefined' ? sessionStorage.getItem('token') : null,

  setAuth: (user, token) => {
    sessionStorage.setItem('token', token);
    set({ user, token });
  },
  setToken: (token) => {
    sessionStorage.setItem('token', token);
    set({ token });
  },

  logout: () => {
    sessionStorage.removeItem('token');
    set({ user: null, token: null });
  },
}));