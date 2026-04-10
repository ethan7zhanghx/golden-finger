import ky from "ky";
import type {
  AuthToken,
  ContextResponse,
  GenerateRequest,
  Project,
  ProjectCreateInput,
  StepAsset,
  StepCode,
  StepResult,
  ToolRunStatus,
  UserLoginInput,
  UserRegisterInput,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export const api = ky.create({
  prefix: API_BASE,
  timeout: 30_000,
  retry: { limit: 2, methods: ["get"] },
  hooks: {
    beforeRequest: [
      ({ request }) => {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("token")
            : null;
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`);
        }
      },
    ],
  },
});

// ── Backend → Frontend type transformations ───

interface AssetOut {
  id: string;
  project_id: string;
  step_code: string;
  asset_type: string;
  title: string | null;
  content: Record<string, unknown> | null;
  is_formal: boolean;
  created_at: string;
  updated_at: string;
}

function assetOutToStepAsset(raw: AssetOut): StepAsset {
  const contentDict = raw.content ?? {};
  // Backend stores content as JSONB: { text: "..." } or { content: "..." }
  const text =
    typeof contentDict.text === "string"
      ? contentDict.text
      : typeof contentDict.content === "string"
        ? contentDict.content
        : JSON.stringify(contentDict);
  return {
    stepCode: raw.step_code as StepCode,
    content: text,
    version: 0,
    updatedAt: raw.updated_at,
  };
}

// ── Auth ──────────────────────────────────────

export async function register(input: UserRegisterInput): Promise<void> {
  await api.post("api/auth/register", { json: input });
}

export async function login(input: UserLoginInput): Promise<AuthToken> {
  const token = await api
    .post("api/auth/login", { json: input })
    .json<AuthToken>();
  localStorage.setItem("token", token.access_token);
  return token;
}

export function logout(): void {
  localStorage.removeItem("token");
}

// ── Project CRUD ──────────────────────────────

export async function listProjects(): Promise<Project[]> {
  return api.get("api/projects").json<Project[]>();
}

export async function getProject(id: string): Promise<Project> {
  return api.get(`api/projects/${id}`).json<Project>();
}

export async function createProject(
  input: ProjectCreateInput,
): Promise<Project> {
  return api.post("api/projects", { json: input }).json<Project>();
}

export async function updateProject(
  id: string,
  input: Partial<ProjectCreateInput & { status?: string; current_step?: StepCode }>,
): Promise<Project> {
  return api.put(`api/projects/${id}`, { json: input }).json<Project>();
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`api/projects/${id}`);
}

// ── Step data ─────────────────────────────────

export async function getStepAsset(
  projectId: string,
  stepCode: StepCode,
): Promise<StepAsset> {
  const raw = await api
    .get(`api/projects/${projectId}/steps/${stepCode}/asset`)
    .json<AssetOut>();
  return assetOutToStepAsset(raw);
}

export async function saveStepAsset(
  projectId: string,
  stepCode: StepCode,
  content: string,
): Promise<StepAsset> {
  const raw = await api
    .patch(`api/projects/${projectId}/steps/${stepCode}/asset`, {
      json: { text: content },
    })
    .json<AssetOut>();
  return assetOutToStepAsset(raw);
}

// ── AI generation (non-stream) ────────────────

export async function generateStep(
  projectId: string,
  stepCode: StepCode,
  request: GenerateRequest,
): Promise<StepResult> {
  return api
    .post(`api/projects/${projectId}/steps/${stepCode}/generate`, {
      json: request,
    })
    .json<StepResult>();
}

// ── AI generation (SSE stream) ────────────────
// Returns the raw Response so the caller can read the event stream.

export async function generateStepStream(
  projectId: string,
  stepCode: StepCode,
  input: Record<string, unknown>,
  options?: { maxTokens?: number; temperature?: number },
): Promise<Response> {
  const body: GenerateRequest = {
    input,
    stream: true,
    max_tokens: options?.maxTokens ?? 4096,
    temperature: options?.temperature ?? 0.7,
  };

  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return fetch(
    `${API_BASE}/api/projects/${projectId}/steps/${stepCode}/generate`,
    {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    },
  );
}

// ── Context ───────────────────────────────────

export async function getStepContext(
  projectId: string,
  stepCode: StepCode,
): Promise<ContextResponse> {
  return api
    .get(`api/projects/${projectId}/steps/${stepCode}/context`)
    .json<ContextResponse>();
}

// ── Tool run actions ──────────────────────────

export async function recordToolRunAction(
  runId: string,
  action: string,
): Promise<void> {
  await api.post(`api/tool-runs/${runId}/action`, { json: { action } });
}

export async function getToolRunStatus(
  runId: string,
): Promise<ToolRunStatus> {
  return api.get(`api/tool-runs/${runId}/status`).json<ToolRunStatus>();
}
