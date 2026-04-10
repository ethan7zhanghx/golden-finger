/* ──────────────────────────────────────────────
 *  Golden-Finger shared TypeScript types
 *  Mirror backend Pydantic schemas + frontend-only types
 * ────────────────────────────────────────────── */

// ── Step definitions ──────────────────────────

export type StepCode =
  | "writing_quality"
  | "market_research"
  | "worldview"
  | "selling_point"
  | "hook"
  | "skeleton"
  | "plot_beats"
  | "character"
  | "narrative"
  | "opening"
  | "dialogue"
  | "pacing"
  | "title"
  | "script_format"
  | "synopsis"
  | "copyright";

export type StepPhase = "prepare" | "plan" | "create" | "finalize";

export interface StepMeta {
  code: StepCode;
  label: string;
  phase: StepPhase;
  phaseLabel: string;
  formType: "form" | "card" | "outline" | "richtext" | "analysis";
}

// ── Project ───────────────────────────────────

export interface Project {
  id: string;
  owner_id?: string;
  title: string;
  genre: string;
  episode_count?: number;
  description?: string;
  status?: string;
  current_step?: StepCode;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  title: string;
  genre: string;
  description?: string;
}

// ── AI / SSE schemas (mirrors backend) ────────

export interface GenerateRequest {
  input: Record<string, unknown>;
  stream: boolean;
  max_tokens?: number;
  temperature?: number;
}

export interface RewriteRequest {
  selected_text: string;
  scene_context: string;
  character_name: string;
  stream?: boolean;
  max_tokens?: number;
  temperature?: number;
}

export type SSEEventType = "start" | "chunk" | "done" | "error";

export interface SSEEvent {
  event: SSEEventType;
  data: Record<string, unknown>;
}

export interface StepResult {
  run_id: string;
  step_code: StepCode;
  status: "queued" | "processing" | "completed" | "failed";
  result: Record<string, unknown>;
  warnings: string[];
}

export interface ContextAsset {
  asset_id: string;
  asset_type: string;
  title: string;
  priority: "required" | "optional";
}

export interface ContextResponse {
  assets: ContextAsset[];
}

export interface ToolRunStatus {
  run_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  result: Record<string, unknown> | null;
}

// ── AI Store types ────────────────────────────

export interface AICandidate {
  id: string;
  runId: string;
  stepCode: StepCode;
  content: string;
  status: "streaming" | "ready" | "accepted" | "rejected";
  createdAt: number;
}

// ── Step asset (saved content) ────────────────

export interface StepAsset {
  stepCode: StepCode;
  content: string;
  version: number;
  updatedAt: string;
}
