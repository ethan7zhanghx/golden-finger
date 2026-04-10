"use client";

import type { ReactNode } from "react";
import { StepNavigation } from "./StepNavigation";
import type { StepCode } from "@/types";

interface WorkbenchLayoutProps {
  projectId: string;
  onStepSelect: (step: StepCode) => void;
  children: ReactNode;
}

/**
 * Two-column workbench layout:
 *   Left  — step navigation (16 steps)
 *   Center — main creation area
 * AI assistant is now a floating FAB handled by StepEditor.
 */
export function WorkbenchLayout({
  projectId,
  onStepSelect,
  children,
}: WorkbenchLayoutProps) {
  return (
    <div className="flex h-screen bg-[#F0EDE8]">
      {/* Left: Step navigation */}
      <StepNavigation projectId={projectId} onStepSelect={onStepSelect} />

      {/* Center: Main creation area — full-width, no max-w constraint */}
      <main className="flex-1 min-w-0 overflow-y-auto bg-[#F0EDE8]">
        {children}
      </main>
    </div>
  );
}
