"use client";

import { useCallback, useState } from "react";
import { Sparkles, X } from "lucide-react";
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
 * Renders a Paper card on the canvas background.
 * AI assistant is a floating FAB that opens an overlay drawer.
 */
export function StepEditor({ projectId, stepCode }: StepEditorProps) {
  const meta = getStepMeta(stepCode);
  const asset = useStepStore((s) => s.assets[stepCode]);
  const updateContent = useStepStore((s) => s.updateContent);
  const [aiOpen, setAIOpen] = useState(false);

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
    <div className="min-h-[calc(100vh-3rem)] bg-[#F0EDE8] px-6 py-0">
      {/* Paper card — professional writing surface */}
      <div
        className="bg-[#FAFAF8] rounded-xl max-w-[720px] mx-auto my-6 min-h-[calc(100vh-5rem)] px-16 py-12 flex flex-col"
        style={{
          boxShadow:
            "0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.03)",
        }}
      >
        {/* Step header */}
        <div className="mb-5 flex items-baseline gap-3">
          <h1 className="text-2xl font-bold text-[#2D2A26] tracking-tight">
            {meta.label}
          </h1>
          <span className="text-sm text-[#9B8F7E]">
            {meta.phaseLabel} · {formTypeLabel(meta.formType)}
          </span>
        </div>

        {/* Writing area */}
        <div className="flex-1 flex flex-col">
          {meta.formType === "richtext" ? (
            <Editor
              content={asset?.content ?? ""}
              onChange={handleContentChange}
              placeholder={`在此编写${meta.label}内容…`}
            />
          ) : (
            <textarea
              className="flex-1 w-full min-h-[calc(100vh-16rem)] bg-transparent resize-none focus:outline-none font-serif text-base leading-relaxed text-[#2D2A26] placeholder:text-[#C0B8AE]"
              style={{ fontFamily: "var(--font-script)" }}
              placeholder={`在此编写${meta.label}内容…`}
              value={asset?.content ?? ""}
              onChange={(e) => handleContentChange(e.target.value)}
            />
          )}
        </div>

        {/* Save status */}
        <div className="mt-4">
          <SaveIndicator stepCode={stepCode} />
        </div>
      </div>

      {/* Floating AI FAB */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setAIOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-[#C8974A] text-white shadow-lg hover:bg-[#B8843A] transition-colors text-sm font-medium"
        >
          <Sparkles className="w-4 h-4" />
          AI 助手
        </button>
      </div>

      {/* AI overlay drawer */}
      {aiOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setAIOpen(false)}
          />
          <div className="fixed right-0 top-0 bottom-0 w-80 z-50 bg-white shadow-2xl border-l border-[#E8E4DC] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-[#E8E4DC]">
              <span className="font-medium text-[#2D2A26] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-[#C8974A]" />
                AI 助手
              </span>
              <button
                onClick={() => setAIOpen(false)}
                className="text-[#9B8F7E] hover:text-[#2D2A26]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
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
        </>
      )}
    </div>
  );
}

function SaveIndicator({ stepCode }: { stepCode: StepCode }) {
  const isDirty = useStepStore((s) => s.dirty[stepCode]);

  return (
    <div className="text-xs text-[#9B8F7E]">
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
