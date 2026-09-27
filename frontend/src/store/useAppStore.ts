import { create } from 'zustand';

interface AppState {
  user: any | null;
  setUser: (user: any) => void;
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: { name: 'Admin User', role: 'admin' },
  setUser: (user) => set({ user }),
  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),
}));
