"use client";

import { create } from "zustand";
import type { AICandidate } from "@/types";

interface AIState {
  candidates: Record<string, AICandidate[]>;
  generating: boolean;
  streamBuffer: string;
  activeRunId: string | null;

  startGeneration: (runId: string) => void;
  appendChunk: (content: string) => void;
  finishGeneration: (stepCode: string) => void;
  failGeneration: () => void;
  acceptCandidate: (stepCode: string, candidateId: string) => void;
  rejectCandidate: (stepCode: string, candidateId: string) => void;
  clearCandidates: (stepCode: string) => void;
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
