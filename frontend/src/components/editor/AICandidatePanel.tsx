"use client";

import { Check, X, Loader2, Sparkles } from "lucide-react";
import type { AICandidate } from "@/types";

interface AICandidatePanelProps {
  stepCode: string;
  candidates: AICandidate[];
  isGenerating: boolean;
  streamContent: string;
  onAccept: (candidateId: string) => void;
  onReject: (candidateId: string) => void;
  onGenerate: () => void;
}

export function AICandidatePanel({
  candidates,
  isGenerating,
  streamContent,
  onAccept,
  onReject,
  onGenerate,
}: AICandidatePanelProps) {
  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-amber-500" />
          AI 助手
        </h3>
        <button
          onClick={onGenerate}
          disabled={isGenerating}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md
            bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" />
              生成中…
            </>
          ) : (
            <>
              <Sparkles className="w-3 h-3" />
              AI 生成
            </>
          )}
        </button>
      </div>

      {/* Streaming preview */}
      {isGenerating && streamContent && (
        <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
          <div className="text-xs text-amber-600 font-medium mb-1 flex items-center gap-1">
            <Loader2 className="w-3 h-3 animate-spin" />
            正在生成…
          </div>
          <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
            {streamContent}
            <span className="inline-block w-1.5 h-4 bg-amber-400 animate-pulse ml-0.5 align-text-bottom" />
          </div>
        </div>
      )}

      {/* Candidate list */}
      <div className="space-y-3">
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.id}
            candidate={candidate}
            onAccept={() => onAccept(candidate.id)}
            onReject={() => onReject(candidate.id)}
          />
        ))}
      </div>

      {!isGenerating && candidates.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-8">
          点击「AI 生成」获取创作建议
        </p>
      )}
    </div>
  );
}

function CandidateCard({
  candidate,
  onAccept,
  onReject,
}: {
  candidate: AICandidate;
  onAccept: () => void;
  onReject: () => void;
}) {
  const isAccepted = candidate.status === "accepted";
  const isRejected = candidate.status === "rejected";
  const isActionable = candidate.status === "ready";

  return (
    <div
      className={`p-3 rounded-lg border text-sm transition-colors ${
        isAccepted
          ? "bg-green-50 border-green-200"
          : isRejected
            ? "bg-gray-50 border-gray-200 opacity-60"
            : "bg-white border-gray-200"
      }`}
    >
      <div className="text-gray-700 whitespace-pre-wrap leading-relaxed mb-2 max-h-40 overflow-y-auto">
        {candidate.content || "(空内容)"}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">
          {isAccepted && "✓ 已采纳"}
          {isRejected && "✗ 已拒绝"}
          {isActionable && "待处理"}
        </span>

        {isActionable && (
          <div className="flex gap-1.5">
            <button
              onClick={onAccept}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded
                bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
            >
              <Check className="w-3 h-3" />
              采纳
            </button>
            <button
              onClick={onReject}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded
                bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
            >
              <X className="w-3 h-3" />
              拒绝
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
