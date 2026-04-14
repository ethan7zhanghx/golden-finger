"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { useEffect, useCallback } from "react";
import { SceneHeading } from "./extensions/SceneHeading";
import { Dialogue } from "./extensions/Dialogue";
import { Action } from "./extensions/Action";
import { Narration } from "./extensions/Narration";

interface EditorProps {
  content: string;
  placeholder?: string;
  onChange: (content: string) => void;
  editable?: boolean;
}

// Script block types with labels, shortcuts and active state detection
const BLOCK_TYPES = [
  {
    name: "sceneHeading",
    label: "场景",
    shortcut: "⌥1",
    placeholder: "第 X 集 · 场景名…",
  },
  {
    name: "dialogue",
    label: "对白",
    shortcut: "⌥2",
    placeholder: "人物名：台词…",
  },
  {
    name: "action",
    label: "动作",
    shortcut: "⌥3",
    placeholder: "动作描写…",
  },
  {
    name: "narration",
    label: "旁白",
    shortcut: "⌥4",
    placeholder: "旁白…",
  },
  {
    name: "paragraph",
    label: "正文",
    shortcut: "⌥0",
    placeholder: "正文…",
  },
] as const;

type BlockTypeName = (typeof BLOCK_TYPES)[number]["name"];

/**
 * 剧本专属富文本编辑器
 * 支持四种剧本块类型：场景头、对白、动作描写、旁白
 * 基于 Tiptap，替代原有通用编辑器
 */
export function Editor({
  content,
  placeholder = "开始创作… 选择右侧块类型或按 Tab 在对白和动作间切换",
  onChange,
  editable = true,
}: EditorProps) {
  const editor = useEditor({
    immediatelyRender: false,
    extensions: [
      StarterKit.configure({
        // 禁用与剧本无关的通用格式
        heading: false,
        bulletList: false,
        orderedList: false,
        codeBlock: false,
        blockquote: false,
        horizontalRule: false,
        strike: false,
        code: false,
      }),
      // 剧本专属块类型
      SceneHeading,
      Dialogue,
      Action,
      Narration,
      Placeholder.configure({
        placeholder: ({ node }) => {
          const match = BLOCK_TYPES.find((b) => b.name === node.type.name);
          return match?.placeholder ?? placeholder;
        },
      }),
    ],
    content,
    editable,
    editorProps: {
      attributes: {
        class:
          "script-editor focus:outline-none min-h-[calc(100vh-18rem)] py-2",
      },
    },
    onUpdate: ({ editor: e }) => {
      onChange(e.getHTML());
    },
  });

  // Sync external content (e.g. accepting an AI candidate)
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, { emitUpdate: false });
    }
  }, [content, editor]);

  const setBlockType = useCallback(
    (typeName: BlockTypeName) => {
      if (!editor) return;
      editor.chain().focus().setNode(typeName).run();
    },
    [editor],
  );

  // Keyboard shortcuts: Alt+1~4,0 for block types
  useEffect(() => {
    if (!editor || !editable) return;
    const handleKey = (e: KeyboardEvent) => {
      if (!e.altKey) return;
      const map: Record<string, BlockTypeName> = {
        "1": "sceneHeading",
        "2": "dialogue",
        "3": "action",
        "4": "narration",
        "0": "paragraph",
      };
      const target = map[e.key];
      if (target) {
        e.preventDefault();
        setBlockType(target);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [editor, editable, setBlockType]);

  return (
    <div className="flex flex-col flex-1">
      {/* Toolbar */}
      {editor && editable && (
        <div className="flex items-center justify-between px-0 py-2 border-b border-[#E8E4DC] bg-transparent">
          {/* Block type switcher */}
          <div className="flex items-center gap-0.5">
            {BLOCK_TYPES.map((bt) => {
              const isActive = editor.isActive(bt.name);
              return (
                <button
                  key={bt.name}
                  type="button"
                  title={`${bt.label} (${bt.shortcut})`}
                  onClick={() => setBlockType(bt.name)}
                  className={`
                    group relative px-2.5 py-1 text-xs rounded transition-all duration-150
                    ${
                      isActive
                        ? "bg-[#2D2A26] text-[#F5E6C8] font-medium"
                        : "text-[#7C6F5B] hover:bg-[#EDE9E2] hover:text-[#2D2A26]"
                    }
                  `}
                >
                  {bt.label}
                  {/* Shortcut tooltip on hover */}
                  <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-[10px] text-[#9B8F7E] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {bt.shortcut}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Inline formatting */}
          <div className="flex items-center gap-0.5">
            <div className="w-px h-3.5 bg-[#E8E4DC] mx-1" />
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleBold().run()}
              className={`
                px-2 py-1 text-xs rounded font-bold transition-colors
                ${editor.isActive("bold") ? "bg-[#F5E6C8] text-[#2D2A26]" : "text-[#9B8F7E] hover:bg-[#EDE9E2]"}
              `}
            >
              B
            </button>
            <button
              type="button"
              onClick={() => editor.chain().focus().toggleItalic().run()}
              className={`
                px-2 py-1 text-xs rounded italic transition-colors
                ${editor.isActive("italic") ? "bg-[#F5E6C8] text-[#2D2A26]" : "text-[#9B8F7E] hover:bg-[#EDE9E2]"}
              `}
            >
              I
            </button>
          </div>
        </div>
      )}

      {/* Keyboard shortcut hint */}
      {editable && (
        <div className="text-[10px] text-[#C0B8AE] py-1.5 flex items-center gap-3">
          <span>Tab — 对白↔动作切换</span>
          <span>Alt+1~4 — 切换块类型</span>
          <span>场景头 Enter — 自动新建动作块</span>
        </div>
      )}

      <EditorContent editor={editor} className="flex-1" />
    </div>
  );
}

// Re-export for use in step pages that need programmatic insertion
export type { EditorProps };
