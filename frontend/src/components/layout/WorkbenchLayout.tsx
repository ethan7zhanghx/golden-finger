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
    <div className="flex h-screen bg-white">
      {/* Left: Step navigation */}
      <StepNavigation projectId={projectId} onStepSelect={onStepSelect} />

      {/* Center: Main creation area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-6">{children}</div>
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
