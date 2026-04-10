import type { StepCode, StepMeta, StepPhase } from "@/types";

const phase = (
  p: StepPhase,
  label: string,
  items: [StepCode, string, StepMeta["formType"]][],
): StepMeta[] =>
  items.map(([code, l, formType]) => ({
    code,
    label: l,
    phase: p,
    phaseLabel: label,
    formType,
  }));

export const STEPS: StepMeta[] = [
  ...phase("prepare", "准备阶段", [
    ["writer_quality", "编剧素质", "form"],
    ["market_research", "扫榜调研", "form"],
  ]),
  ...phase("plan", "策划阶段", [
    ["worldview", "世界观设定", "card"],
    ["selling_point", "提炼核心卖点", "card"],
    ["hook", "爽点和钩子", "card"],
    ["skeleton", "骨骼框架", "outline"],
  ]),
  ...phase("create", "创作阶段", [
    ["plot_beats", "剧情和桥段", "outline"],
    ["character", "人物写作", "card"],
    ["narrative", "叙事方法", "card"],
    ["opening", "开头写作", "richtext"],
    ["dialogue", "台词写作", "richtext"],
    ["rhythm", "节奏控制", "analysis"],
  ]),
  ...phase("finalize", "完善阶段", [
    ["title", "剧名创作", "card"],
    ["script_format", "剧本格式", "analysis"],
    ["synopsis", "剧本介绍", "richtext"],
    ["copyright", "版权证书", "analysis"],
  ]),
];

export function getStepMeta(code: StepCode): StepMeta {
  return STEPS.find((s) => s.code === code) ?? STEPS[0];
}

export function getPhaseSteps(phaseKey: StepPhase): StepMeta[] {
  return STEPS.filter((s) => s.phase === phaseKey);
}

export const PHASES: { key: StepPhase; label: string }[] = [
  { key: "prepare", label: "准备阶段" },
  { key: "plan", label: "策划阶段" },
  { key: "create", label: "创作阶段" },
  { key: "finalize", label: "完善阶段" },
];
