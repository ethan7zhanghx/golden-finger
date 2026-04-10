"use client";

import { useCallback, useEffect, useRef } from "react";
import { createOrUpdateAsset } from "@/lib/api";
import { useStepStore } from "@/stores/stepStore";

const DEBOUNCE_MS = 500;

/**
 * Auto-saves step content with a 500ms debounce.
 *
 * Watches the step store for dirty flags and persists when
 * the user stops typing.
 */
export function useAutoSave(projectId: string, stepCode: string) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savingRef = useRef(false);

  const save = useCallback(async () => {
    if (savingRef.current) return;

    const state = useStepStore.getState();
    const asset = state.assets[stepCode];
    const isDirty = state.dirty[stepCode];

    if (!asset || !isDirty) return;

    savingRef.current = true;
    try {
      const saved = await createOrUpdateAsset(projectId, {
        step_code: stepCode,
        asset_type: "step_content",
        title: stepCode,
        content: { text: asset.content },
      });
      useStepStore.getState().setAsset(stepCode, {
        stepCode,
        content: (saved.content?.text as string) ?? asset.content,
        version: saved.version,
        updatedAt: saved.updated_at ?? saved.created_at,
      });
    } catch (err) {
      console.error("[auto-save] failed:", err);
    } finally {
      savingRef.current = false;
    }
  }, [projectId, stepCode]);

  const scheduleSave = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(save, DEBOUNCE_MS);
  }, [save]);

  // Subscribe to dirty changes
  useEffect(() => {
    const unsub = useStepStore.subscribe((state, prev) => {
      if (state.dirty[stepCode] && !prev.dirty[stepCode]) {
        scheduleSave();
      }
    });

    return () => {
      unsub();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [stepCode, scheduleSave]);

  // Save on unmount if dirty
  useEffect(() => {
    return () => {
      const isDirty = useStepStore.getState().dirty[stepCode];
      if (isDirty) save();
    };
  }, [stepCode, save]);

  return { saveNow: save };
}
