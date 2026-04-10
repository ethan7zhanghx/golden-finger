"use client";

import type { ReactNode } from "react";
import { StepNavigation } from "./StepNavigation";
import type { StepCode } from "@/types";

interface WorkbenchLayoutProps {
  projectId: string;
  onStepSelect: (step: StepCode) => void;
  children: ReactNode;
  assistantPanel?: ReactNode;
}

/**
 * Three-column workbench layout:
 *   Left  — step navigation (16 steps)
 *   Center — main creation area
 *   Right  — AI assistant / context panel
 */
export function WorkbenchLayout({
  projectId,
  onStepSelect,
  children,
  assistantPanel,
}: WorkbenchLayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left: Step navigation */}
      <StepNavigation projectId={projectId} onStepSelect={onStepSelect} />

      {/* Center: Main creation area — full-width, no max-w constraint */}
      <main className="flex-1 min-w-0 overflow-y-auto bg-gray-50">
        {children}
      </main>

      {/* Right: Assistant panel */}
      {assistantPanel && (
        <aside className="w-80 shrink-0 border-l border-gray-200 bg-gray-50 overflow-y-auto">
          {assistantPanel}
        </aside>
      )}
    </div>
  );
}
