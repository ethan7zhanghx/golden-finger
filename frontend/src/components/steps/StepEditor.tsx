"use client";

import { useCallback } from "react";
import { Editor } from "@/components/editor/Editor";
import { AICandidatePanel } from "@/components/editor/AICandidatePanel";
import { useAIGenerate } from "@/hooks/useAIGenerate";
import { useAutoSave } from "@/hooks/useAutoSave";
import { useStepStore } from "@/stores/stepStore";
import { getStepMeta } from "@/lib/steps";
import type { StepCode } from "@/types";

interface StepEditorProps {
  projectId: string;
  stepCode: StepCode;
}

/**
 * The main step editor component.
 * Renders the editor in the center and the AI candidate panel on the right.
 */
export function StepEditor({ projectId, stepCode }: StepEditorProps) {
  const meta = getStepMeta(stepCode);
  const asset = useStepStore((s) => s.assets[stepCode]);
  const updateContent = useStepStore((s) => s.updateContent);

  // Auto-save
  useAutoSave(projectId, stepCode);

  // AI generation
  const {
    generate,
    accept,
    reject,
    isGenerating,
    streamContent,
    candidates,
  } = useAIGenerate({ projectId, stepCode });

  const handleContentChange = useCallback(
    (content: string) => {
      updateContent(stepCode, content);
    },
    [stepCode, updateContent],
  );

  const handleAccept = useCallback(
    (candidateId: string) => {
      const candidate = candidates.find((c) => c.id === candidateId);
      if (candidate) {
        // Write accepted content into the step asset
        updateContent(stepCode, candidate.content);
        accept(candidateId);
      }
    },
    [candidates, stepCode, updateContent, accept],
  );

  const handleGenerate = useCallback(() => {
    generate({ step: stepCode, current_content: asset?.content ?? "" });
  }, [generate, stepCode, asset]);

  return (
    <div className="flex min-h-[calc(100vh-3rem)]">
      {/* Center: Writing area — fills all available space */}
      <div className="flex-1 min-w-0 flex flex-col px-10 py-8">
        {/* Step header */}
        <div className="mb-5 flex items-baseline gap-3">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            {meta.label}
          </h1>
          <span className="text-sm text-gray-400">
            {meta.phaseLabel} · {formTypeLabel(meta.formType)}
          </span>
        </div>

        {/* Paper card — mimics a professional writing surface */}
        <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {meta.formType === "richtext" ? (
            <Editor
              content={asset?.content ?? ""}
              onChange={handleContentChange}
              placeholder={`在此编写${meta.label}内容…`}
            />
          ) : (
            <textarea
              className="flex-1 w-full min-h-[calc(100vh-16rem)] p-8 text-base
                leading-relaxed resize-none focus:outline-none bg-transparent
                placeholder:text-gray-300"
              placeholder={`在此编写${meta.label}内容…`}
              value={asset?.content ?? ""}
              onChange={(e) => handleContentChange(e.target.value)}
            />
          )}
        </div>

        {/* Save status */}
        <div className="mt-2">
          <SaveIndicator stepCode={stepCode} />
        </div>
      </div>

      {/* Right: AI assistant panel */}
      <div className="w-72 shrink-0 border-l border-gray-200 bg-white overflow-y-auto">
        <AICandidatePanel
          stepCode={stepCode}
          candidates={candidates}
          isGenerating={isGenerating}
          streamContent={streamContent}
          onAccept={handleAccept}
          onReject={reject}
          onGenerate={handleGenerate}
        />
      </div>
    </div>
  );
}

function SaveIndicator({ stepCode }: { stepCode: StepCode }) {
  const isDirty = useStepStore((s) => s.dirty[stepCode]);

  return (
    <div className="mt-2 text-xs text-gray-400">
      {isDirty ? "未保存的更改…" : "已保存"}
    </div>
  );
}

function formTypeLabel(formType: string): string {
  const map: Record<string, string> = {
    form: "表单输入",
    card: "卡片编辑",
    outline: "大纲编辑",
    richtext: "正文编辑",
    analysis: "分析报告",
  };
  return map[formType] ?? formType;
}
