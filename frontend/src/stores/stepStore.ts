"use client";

import { create } from "zustand";
import type { StepCode, StepAsset } from "@/types";

interface StepState {
  /** Cached step assets keyed by stepCode */
  assets: Partial<Record<StepCode, StepAsset>>;
  /** Currently active step */
  activeStep: StepCode;
  /** Dirty flag per step (unsaved local changes) */
  dirty: Partial<Record<StepCode, boolean>>;
  /** Step completion status */
  completed: Partial<Record<StepCode, boolean>>;

  setActiveStep: (step: StepCode) => void;
  setAsset: (step: StepCode, asset: StepAsset) => void;
  updateContent: (step: StepCode, content: string) => void;
  markDirty: (step: StepCode, dirty: boolean) => void;
  markCompleted: (step: StepCode, completed: boolean) => void;
}

export const useStepStore = create<StepState>((set) => ({
  assets: {},
  activeStep: "worldview",
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
