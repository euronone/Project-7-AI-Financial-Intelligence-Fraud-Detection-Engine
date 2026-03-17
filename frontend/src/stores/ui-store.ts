import { create } from "zustand";

interface UiState {
  sidebarCollapsed: boolean;
  sidebarMobileOpen: boolean;
  theme: "light" | "dark";

  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleMobileSidebar: () => void;
  closeMobileSidebar: () => void;
  setTheme: (theme: "light" | "dark") => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  sidebarMobileOpen: false,
  theme: "light",

  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
  toggleMobileSidebar: () => set((s) => ({ sidebarMobileOpen: !s.sidebarMobileOpen })),
  closeMobileSidebar: () => set({ sidebarMobileOpen: false }),
  setTheme: (theme) => set({ theme }),
}));
