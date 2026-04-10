"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { WorkbenchLayout } from "@/components/layout/WorkbenchLayout";
import { StepEditor } from "@/components/steps/StepEditor";
import { useStepStore } from "@/stores/stepStore";
import { listAssets } from "@/lib/api";

export default function StepPage() {
  const params = useParams<{ id: string; step: string }>();
  const router = useRouter();
  const projectId = params.id;
  const stepCode = params.step;

  const setActiveStep = useStepStore((s) => s.setActiveStep);
  const setAsset = useStepStore((s) => s.setAsset);
  const existingAsset = useStepStore((s) => s.assets[stepCode]);

  // Set active step on mount / step change
  useEffect(() => {
    setActiveStep(stepCode);
  }, [stepCode, setActiveStep]);

  // Load step asset from backend
  useEffect(() => {
    if (existingAsset) return;

    listAssets(projectId)
      .then((assets) => {
        const match = assets.find(
          (a) => a.step_code === stepCode && a.asset_type === "step_content",
        );
        if (match) {
          setAsset(stepCode, {
            stepCode,
            content: (match.content?.text as string) ?? "",
            version: match.version,
            updatedAt: match.updated_at ?? match.created_at,
          });
        } else {
          setAsset(stepCode, {
            stepCode,
            content: "",
            version: 0,
            updatedAt: new Date().toISOString(),
          });
        }
      })
      .catch(() => {
        setAsset(stepCode, {
          stepCode,
          content: "",
          version: 0,
          updatedAt: new Date().toISOString(),
        });
      });
  }, [projectId, stepCode, existingAsset, setAsset]);

  const handleStepSelect = (step: string) => {
    router.push(`/projects/${projectId}/steps/${step}`);
  };

  return (
    <WorkbenchLayout projectId={projectId} onStepSelect={handleStepSelect}>
      <StepEditor projectId={projectId} stepCode={stepCode} />
    </WorkbenchLayout>
  );
}
