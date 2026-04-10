import ky from "ky";
import type {
  ContextResponse,
  GenerateRequest,
  Project,
  ProjectCreateInput,
  StepAsset,
  StepCode,
  StepResult,
  ToolRunStatus,
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

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`api/projects/${id}`);
}

// ── Step data ─────────────────────────────────

export async function getStepAsset(
  projectId: string,
  stepCode: StepCode,
): Promise<StepAsset> {
  return api
    .get(`api/projects/${projectId}/steps/${stepCode}/asset`)
    .json<StepAsset>();
}

export async function saveStepAsset(
  projectId: string,
  stepCode: StepCode,
  content: string,
): Promise<StepAsset> {
  return api
    .patch(`api/projects/${projectId}/steps/${stepCode}/asset`, {
      json: { content },
    })
    .json<StepAsset>();
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
