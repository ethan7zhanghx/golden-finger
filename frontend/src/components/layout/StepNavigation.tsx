"use client";

import { useStepStore } from "@/stores/stepStore";
import { PHASES, getPhaseSteps } from "@/lib/steps";
import { CheckCircle2, Circle } from "lucide-react";

interface StepNavigationProps {
  projectId: string;
  onStepSelect: (step: string) => void;
}

export function StepNavigation({ onStepSelect }: StepNavigationProps) {
  const activeStep = useStepStore((s) => s.activeStep);
  const completed = useStepStore((s) => s.completed);

  return (
    <nav className="w-64 shrink-0 border-r border-gray-200 bg-gray-50 overflow-y-auto">
      <div className="px-4 py-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
          创作流程
        </h2>

        {PHASES.map((phase) => (
          <div key={phase.key} className="mb-5">
            <h3 className="text-xs font-medium text-gray-400 mb-2 px-2">
              {phase.label}
            </h3>
            <ul className="space-y-0.5">
              {getPhaseSteps(phase.key).map((step) => {
                const isActive = step.code === activeStep;
                const isDone = completed[step.code];
                return (
                  <li key={step.code}>
                    <button
                      onClick={() => onStepSelect(step.code)}
                      className={`
                        w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors
                        ${isActive
                          ? "bg-amber-50 text-amber-900 font-medium"
                          : "text-gray-700 hover:bg-gray-100"}
                      `}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                      ) : (
                        <Circle
                          className={`w-4 h-4 shrink-0 ${
                            isActive ? "text-amber-500" : "text-gray-300"
                          }`}
                        />
                      )}
                      <span className="truncate">{step.label}</span>
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
