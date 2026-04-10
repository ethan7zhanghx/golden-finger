"use client";

import { useStepStore } from "@/stores/stepStore";
import { PHASES, getPhaseSteps } from "@/lib/steps";
import { CheckCircle2, Circle } from "lucide-react";
import type { StepCode } from "@/types";

interface StepNavigationProps {
  projectId: string;
  onStepSelect: (step: StepCode) => void;
}

export function StepNavigation({ onStepSelect }: StepNavigationProps) {
  const activeStep = useStepStore((s) => s.activeStep);
  const completed = useStepStore((s) => s.completed);

  return (
    <nav className="w-56 shrink-0 border-r border-gray-200 bg-white overflow-y-auto">
      <div className="px-3 py-4">
        <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest mb-3 px-2">
          创作流程
        </p>

        {PHASES.map((phase) => (
          <div key={phase.key} className="mb-4">
            <p className="text-[10px] font-semibold text-gray-400 mb-1 px-2 uppercase tracking-wider">
              {phase.label}
            </p>
            <ul className="space-y-px">
              {getPhaseSteps(phase.key).map((step) => {
                const isActive = step.code === activeStep;
                const isDone = completed[step.code];
                return (
                  <li key={step.code}>
                    <button
                      onClick={() => onStepSelect(step.code)}
                      className={`
                        w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-all
                        ${isActive
                          ? "bg-amber-50 text-amber-800 font-medium"
                          : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"}
                      `}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      ) : (
                        <Circle
                          className={`w-3.5 h-3.5 shrink-0 ${
                            isActive ? "text-amber-400" : "text-gray-200"
                          }`}
                        />
                      )}
                      <span className="truncate text-[13px]">{step.label}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </nav>
  );
}
