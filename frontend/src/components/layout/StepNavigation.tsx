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
    <nav className="w-56 shrink-0 border-r border-[#E8E4DC] bg-[#F7F4EF] overflow-y-auto">
      <div className="px-3 py-4">
        <p className="text-[11px] font-semibold text-[#9B8F7E] uppercase tracking-widest mb-3 px-2">
          创作流程
        </p>

        {PHASES.map((phase) => (
          <div key={phase.key} className="mb-4">
            <p className="text-[10px] font-semibold text-[#9B8F7E] mb-1 px-2 uppercase tracking-wider">
              {phase.label}
            </p>
            <ul className="space-y-px">
              {getPhaseSteps(phase.key).map((step) => {
                const isActive = step.code === activeStep;
                const isDone = completed[step.code];
                return (
                  <li key={step.code} className="relative">
                    {isActive && (
                      <span className="absolute left-0 top-[20%] h-[60%] w-0.5 bg-[#C8974A] rounded-r" />
                    )}
                    <button
                      onClick={() => onStepSelect(step.code)}
                      className={`
                        w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-all
                        ${isActive
                          ? "bg-[#F5E6C8] text-[#2D2A26] font-medium"
                          : "text-[#7C6F5B] hover:bg-[#EDE9E2] hover:text-[#2D2A26]"}
                      `}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#4A7C59] shrink-0" />
                      ) : (
                        <Circle
                          className={`w-3.5 h-3.5 shrink-0 ${
                            isActive ? "text-[#C8974A]" : "text-[#9B8F7E]"
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
