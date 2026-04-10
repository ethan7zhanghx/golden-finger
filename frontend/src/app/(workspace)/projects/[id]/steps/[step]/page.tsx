"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { WorkbenchLayout } from "@/components/layout/WorkbenchLayout";
import { StepEditor } from "@/components/steps/StepEditor";
import { useStepStore } from "@/stores/stepStore";
import { getStepAsset } from "@/lib/api";
import type { StepCode } from "@/types";

export default function StepPage() {
  const params = useParams<{ id: string; step: string }>();
  const router = useRouter();
  const projectId = params.id;
  const stepCode = params.step as StepCode;

  const setActiveStep = useStepStore((s) => s.setActiveStep);
  const setAsset = useStepStore((s) => s.setAsset);
  const existingAsset = useStepStore((s) => s.assets[stepCode]);

  // Set active step on mount / step change
  useEffect(() => {
    setActiveStep(stepCode);
  }, [stepCode, setActiveStep]);

  // Load step asset from backend
  useEffect(() => {
    if (existingAsset) return; // already cached

    getStepAsset(projectId, stepCode)
      .then((asset) => setAsset(stepCode, asset))
      .catch(() => {
        // Backend not ready — initialize with empty content
        setAsset(stepCode, {
          stepCode,
          content: "",
          version: 0,
          updatedAt: new Date().toISOString(),
        });
      });
  }, [projectId, stepCode, existingAsset, setAsset]);

  const handleStepSelect = (step: StepCode) => {
    router.push(`/projects/${projectId}/steps/${step}`);
  };

  return (
    <WorkbenchLayout projectId={projectId} onStepSelect={handleStepSelect}>
      <StepEditor projectId={projectId} stepCode={stepCode} />
    </WorkbenchLayout>
  );
}
