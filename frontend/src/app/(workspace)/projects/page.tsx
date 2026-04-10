"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { listProjects, createProject } from "@/lib/api";
import { useProjectStore } from "@/stores/projectStore";
import { Plus, FolderOpen } from "lucide-react";
import type { Project } from "@/types";

export default function ProjectsPage() {
  const router = useRouter();
  const { projects, setProjects } = useProjectStore();
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.replace("/login");
      return;
    }
    listProjects()
      .then(setProjects)
      .catch(() => {
        setProjects([]);
      })
      .finally(() => setLoading(false));
  }, [setProjects]);

  const handleCreate = async () => {
    if (!title.trim()) return;
    try {
      const project = await createProject({ title, genre });
      setProjects([project, ...projects]);
      setTitle("");
      setGenre("");
      setCreating(false);
      router.push(`/projects/${project.id}/steps/worldview`);
    } catch {
      // If backend is not available, create a mock project for demo
      const mock: Project = {
        id: crypto.randomUUID(),
        title,
        genre,
        current_step: "worldview",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setProjects([mock, ...projects]);
      setTitle("");
      setGenre("");
      setCreating(false);
      router.push(`/projects/${mock.id}/steps/worldview`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        加载中…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F0EDE8] px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-[#2D2A26] tracking-tight">我的项目</h1>
            <p className="text-sm text-[#9B8F7E] mt-1">管理你的剧本创作项目</p>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg
              bg-[#C8974A] text-white hover:bg-[#B8843A] transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            新建项目
          </button>
        </div>

        {/* Create dialog (inline) */}
        {creating && (
          <div className="mb-6 p-5 rounded-xl bg-[#FAFAF8] shadow-[0_2px_8px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.03)]">
            <h2 className="text-sm font-semibold text-[#2D2A26] mb-4">新建项目</h2>
            <div className="space-y-3">
              <input
                type="text"
                placeholder="项目标题"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2.5 text-sm border border-[#E8E4DC] rounded-lg bg-white
                  focus:outline-none focus:ring-2 focus:ring-[#C8974A]/30 focus:border-[#C8974A]
                  text-[#2D2A26] placeholder:text-[#C0B8AE]"
              />
              <input
                type="text"
                placeholder="题材类型（如：悬疑、甜宠、逆袭）"
                value={genre}
                onChange={(e) => setGenre(e.target.value)}
                className="w-full px-3 py-2.5 text-sm border border-[#E8E4DC] rounded-lg bg-white
                  focus:outline-none focus:ring-2 focus:ring-[#C8974A]/30 focus:border-[#C8974A]
                  text-[#2D2A26] placeholder:text-[#C0B8AE]"
              />
              <div className="flex gap-2 pt-1">
                <button
                  onClick={handleCreate}
                  className="px-4 py-1.5 text-sm bg-[#C8974A] text-white rounded-lg hover:bg-[#B8843A] transition-colors"
                >
                  创建
                </button>
                <button
                  onClick={() => setCreating(false)}
                  className="px-4 py-1.5 text-sm text-[#7C6F5B] hover:text-[#2D2A26] transition-colors"
                >
                  取消
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project list */}
        {projects.length === 0 ? (
          <div className="text-center py-20">
            <FolderOpen className="w-12 h-12 mx-auto mb-3 text-[#C0B8AE]" />
            <p className="text-[#9B8F7E] text-sm">还没有项目，点击「新建项目」开始创作</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() =>
                  router.push(
                    `/projects/${project.id}/steps/${project.current_step ?? "worldview"}`,
                  )
                }
                className="text-left p-5 rounded-xl bg-[#FAFAF8]
                  shadow-[0_2px_8px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.03)]
                  hover:shadow-[0_4px_16px_rgba(0,0,0,0.10),0_0_0_1px_rgba(200,151,74,0.3)]
                  transition-all group"
              >
                <h3 className="font-semibold text-[#2D2A26] group-hover:text-[#C8974A] transition-colors">
                  {project.title}
                </h3>
                <p className="text-xs text-[#9B8F7E] mt-1.5">
                  {project.genre || "未分类"} · {project.status ?? "draft"}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
