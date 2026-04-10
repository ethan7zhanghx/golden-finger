"use client";

import { create } from "zustand";
import type { StepAsset } from "@/types";

interface StepState {
  assets: Record<string, StepAsset>;
  activeStep: string;
  dirty: Record<string, boolean>;
  completed: Record<string, boolean>;

  setActiveStep: (step: string) => void;
  setAsset: (step: string, asset: StepAsset) => void;
  updateContent: (step: string, content: string) => void;
  markDirty: (step: string, dirty: boolean) => void;
  markCompleted: (step: string, completed: boolean) => void;
}

export const useStepStore = create<StepState>((set) => ({
  assets: {},
  activeStep: "concept",
  dirty: {},
  completed: {},

  setActiveStep: (step) => set({ activeStep: step }),

  setAsset: (step, asset) =>
    set((state) => ({
      assets: { ...state.assets, [step]: asset },
      dirty: { ...state.dirty, [step]: false },
    })),

  updateContent: (step, content) =>
    set((state) => {
      const existing = state.assets[step];
      if (!existing) return state;
      return {
        assets: {
          ...state.assets,
          [step]: { ...existing, content },
        },
        dirty: { ...state.dirty, [step]: true },
      };
    }),

  markDirty: (step, dirty) =>
    set((state) => ({ dirty: { ...state.dirty, [step]: dirty } })),

  markCompleted: (step, completed) =>
    set((state) => ({
      completed: { ...state.completed, [step]: completed },
    })),
}));
