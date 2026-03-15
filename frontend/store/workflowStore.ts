import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface WorkflowStore {
  // Current workflow ID
  currentWorkflowId: string | null;
  setCurrentWorkflowId: (id: string | null) => void;
  
  // Demo mode
  demoMode: boolean;
  toggleDemoMode: () => void;
  setDemoMode: (enabled: boolean) => void;
  
  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  
  // Filters
  skillFilters: string[];
  setSkillFilters: (skills: string[]) => void;
  experienceRange: [number, number];
  setExperienceRange: (range: [number, number]) => void;
  
  // Reset
  reset: () => void;
}

const initialState = {
  currentWorkflowId: null,
  demoMode: process.env.NEXT_PUBLIC_DEMO_MODE === 'true',
  sidebarOpen: true,
  skillFilters: [],
  experienceRange: [0, 20] as [number, number],
};

export const useWorkflowStore = create<WorkflowStore>()(
  devtools(
    (set) => ({
      ...initialState,
      
      setCurrentWorkflowId: (id) => set({ currentWorkflowId: id }),
      
      toggleDemoMode: () => set((state) => ({ demoMode: !state.demoMode })),
      setDemoMode: (enabled) => set({ demoMode: enabled }),
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      
      setSkillFilters: (skills) => set({ skillFilters: skills }),
      setExperienceRange: (range) => set({ experienceRange: range }),
      
      reset: () => set(initialState),
    }),
    { name: 'WorkflowStore' }
  )
);
