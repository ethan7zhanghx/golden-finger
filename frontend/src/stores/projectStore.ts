"use client";

import { create } from "zustand";
import type { Project } from "@/types";

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  updateCurrentStep: (step: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  updateCurrentStep: (step) =>
    set((state) => ({
      currentProject: state.currentProject
        ? { ...state.currentProject, current_step_code: step }
        : null,
    })),
}));
