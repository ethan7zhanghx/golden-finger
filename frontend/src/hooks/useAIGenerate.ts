"use client";

import { useCallback } from "react";
import { generateStepStream, recordToolRunAction } from "@/lib/api";
import { useAIStore } from "@/stores/aiStore";
import { useSSE } from "./useSSE";
interface UseAIGenerateOptions {
  projectId: string;
  stepCode: string;
}

/**
 * Hook that wires SSE streaming to the AI store.
 *
 * Usage:
 *   const { generate, isGenerating, streamContent } = useAIGenerate({ projectId, stepCode });
 *   <button onClick={() => generate({ genre: "悬疑" })}>AI 生成</button>
 */
export function useAIGenerate({ projectId, stepCode }: UseAIGenerateOptions) {
  const {
    generating,
    streamBuffer,
    startGeneration,
    appendChunk,
    finishGeneration,
    failGeneration,
  } = useAIStore();

  const { consume, abort } = useSSE({
    onStart: (data) => {
      const runId = (data.run_id as string) ?? "";
      startGeneration(runId);
    },
    onChunk: (data) => {
      const content = (data.content as string) ?? "";
      if (content) appendChunk(content);
    },
    onDone: () => {
      finishGeneration(stepCode);
    },
    onError: (data) => {
      console.error("[AI generate] SSE error:", data);
      failGeneration();
    },
  });

  const generate = useCallback(
    async (input: Record<string, unknown> = {}) => {
      try {
        const response = await generateStepStream(projectId, stepCode, input);

        if (!response.ok) {
          console.error("Generate request failed:", response.status);
          failGeneration();
          return;
        }

        await consume(response);
      } catch (err) {
        console.error("[AI generate] error:", err);
        failGeneration();
      }
    },
    [projectId, stepCode, consume, failGeneration],
  );

  const accept = useCallback(
    async (candidateId: string) => {
      const candidates = useAIStore.getState().candidates[stepCode] ?? [];
      const candidate = candidates.find((c) => c.id === candidateId);
      if (!candidate) return;

      useAIStore.getState().acceptCandidate(stepCode, candidateId);
      await recordToolRunAction(candidate.runId, "accept").catch(() => {});
    },
    [stepCode],
  );

  const reject = useCallback(
    async (candidateId: string) => {
      const candidates = useAIStore.getState().candidates[stepCode] ?? [];
      const candidate = candidates.find((c) => c.id === candidateId);
      if (!candidate) return;

      useAIStore.getState().rejectCandidate(stepCode, candidateId);
      await recordToolRunAction(candidate.runId, "reject").catch(() => {});
    },
    [stepCode],
  );

  return {
    generate,
    accept,
    reject,
    abort,
    isGenerating: generating,
    streamContent: streamBuffer,
    candidates: useAIStore((s) => s.candidates[stepCode] ?? []),
  };
}
