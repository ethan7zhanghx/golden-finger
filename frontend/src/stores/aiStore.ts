"use client";

import { create } from "zustand";
import type { AICandidate, StepCode } from "@/types";

interface AIState {
  /** All candidates keyed by stepCode */
  candidates: Partial<Record<StepCode, AICandidate[]>>;
  /** Whether AI generation is in progress */
  generating: boolean;
  /** Current streaming content buffer */
  streamBuffer: string;
  /** Active run ID */
  activeRunId: string | null;

  startGeneration: (runId: string) => void;
  appendChunk: (content: string) => void;
  finishGeneration: (stepCode: StepCode) => void;
  failGeneration: () => void;
  acceptCandidate: (stepCode: StepCode, candidateId: string) => void;
  rejectCandidate: (stepCode: StepCode, candidateId: string) => void;
  clearCandidates: (stepCode: StepCode) => void;
}

export const useAIStore = create<AIState>((set) => ({
  candidates: {},
  generating: false,
  streamBuffer: "",
  activeRunId: null,

  startGeneration: (runId) =>
    set({ generating: true, streamBuffer: "", activeRunId: runId }),

  appendChunk: (content) =>
    set((state) => ({ streamBuffer: state.streamBuffer + content })),

  finishGeneration: (stepCode) =>
    set((state) => {
      const candidate: AICandidate = {
        id: crypto.randomUUID(),
        runId: state.activeRunId ?? "",
        stepCode,
        content: state.streamBuffer,
        status: "ready",
        createdAt: Date.now(),
      };
      const existing = state.candidates[stepCode] ?? [];
      return {
        generating: false,
        streamBuffer: "",
        activeRunId: null,
        candidates: {
          ...state.candidates,
          [stepCode]: [candidate, ...existing],
        },
      };
    }),

  failGeneration: () =>
    set({ generating: false, streamBuffer: "", activeRunId: null }),

  acceptCandidate: (stepCode, candidateId) =>
    set((state) => {
      const list = state.candidates[stepCode] ?? [];
      return {
        candidates: {
          ...state.candidates,
          [stepCode]: list.map((c) =>
            c.id === candidateId ? { ...c, status: "accepted" as const } : c,
          ),
        },
      };
    }),

  rejectCandidate: (stepCode, candidateId) =>
    set((state) => {
      const list = state.candidates[stepCode] ?? [];
      return {
        candidates: {
          ...state.candidates,
          [stepCode]: list.map((c) =>
            c.id === candidateId ? { ...c, status: "rejected" as const } : c,
          ),
        },
      };
    }),

  clearCandidates: (stepCode) =>
    set((state) => ({
      candidates: { ...state.candidates, [stepCode]: [] },
    })),
}));
