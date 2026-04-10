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
    listProjects()
      .then(setProjects)
      .catch(() => {
        // Backend not ready — show empty state
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
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">我的项目</h1>
        <button
          onClick={() => setCreating(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md
            bg-amber-500 text-white hover:bg-amber-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          新建项目
        </button>
      </div>

      {/* Create dialog (inline) */}
      {creating && (
        <div className="mb-6 p-4 border border-amber-200 rounded-lg bg-amber-50">
          <h2 className="text-sm font-semibold mb-3">新建项目</h2>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="项目标题"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md
                focus:outline-none focus:ring-2 focus:ring-amber-200"
            />
            <input
              type="text"
              placeholder="题材类型（如：悬疑、甜宠、逆袭）"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md
                focus:outline-none focus:ring-2 focus:ring-amber-200"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                className="px-4 py-1.5 text-sm bg-amber-500 text-white rounded-md hover:bg-amber-600"
              >
                创建
              </button>
              <button
                onClick={() => setCreating(false)}
                className="px-4 py-1.5 text-sm text-gray-600 hover:text-gray-800"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Project list */}
      {projects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <FolderOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>还没有项目，点击「新建项目」开始创作</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {projects.map((project) => (
            <button
              key={project.id}
              onClick={() =>
                router.push(
                  `/projects/${project.id}/steps/${project.current_step}`,
                )
              }
              className="text-left p-4 border border-gray-200 rounded-lg hover:border-amber-300
                hover:shadow-sm transition-all bg-white"
            >
              <h3 className="font-medium text-gray-900">{project.title}</h3>
              <p className="text-xs text-gray-400 mt-1">
                {project.genre} · 当前步骤: {project.current_step}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
