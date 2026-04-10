/* ──────────────────────────────────────────────
 *  Golden-Finger shared TypeScript types
 *  Mirror backend Pydantic schemas + frontend-only types
 * ────────────────────────────────────────────── */

// ── Step definitions ──────────────────────────

export type StepCode =
  | "concept"
  | "outline"
  | "characters"
  | "scenes"
  | "writer-quality"
  | "worldview"
  | "selling_point"
  | "hook"
  | "skeleton"
  | "plot_beats"
  | "character"
  | "narrative"
  | "opening"
  | "dialogue"
  | "rhythm"
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

// ── Auth ──────────────────────────────────────

export interface AuthToken {
  access_token: string;
}

export interface UserRegisterInput {
  email: string;
  password: string;
}

export interface UserLoginInput {
  email: string;
  password: string;
}

// ── Project (mirrors backend ProjectRead) ─────

export interface Project {
  id: string;
  title: string;
  genre: string | null;
  description: string | null;
  status: string;
  current_step_code: string;
  created_at: string;
  updated_at: string | null;
}

export interface ProjectCreateInput {
  title: string;
  genre?: string;
  description?: string;
}

export interface ProjectUpdateInput {
  title?: string;
  genre?: string;
  description?: string;
  status?: string;
  current_step_code?: string;
}

// ── Step progress (mirrors backend StepProgressRead) ──

export interface StepProgress {
  id: string;
  step_code: string;
  step_name: string;
  status: string;
  progress_percent: number;
  is_current: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}

// ── Asset (mirrors backend AssetRead) ─────────

export interface Asset {
  id: string;
  project_id: string;
  step_code: string;
  asset_type: string;
  title: string | null;
  content: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface AssetCreateInput {
  step_code: string;
  asset_type: string;
  title?: string;
  content: Record<string, unknown>;
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
  step_code: string;
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
  stepCode: string;
  content: string;
  status: "streaming" | "ready" | "accepted" | "rejected";
  createdAt: number;
}

// ── Step asset (frontend convenience wrapper) ──

export interface StepAsset {
  stepCode: string;
  content: string;
  version: number;
  updatedAt: string;
}
