"use client";

import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import { useEffect, useCallback } from "react";

interface EditorProps {
  content: string;
  placeholder?: string;
  onChange: (content: string) => void;
  editable?: boolean;
}

/**
 * TipTap headless editor with minimal styling.
 * Used for richtext steps (opening, dialogue, synopsis).
 */
export function Editor({
  content,
  placeholder = "开始创作…",
  onChange,
  editable = true,
}: EditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({ placeholder }),
    ],
    content,
    editable,
    editorProps: {
      attributes: {
        class:
          "prose prose-sm max-w-none focus:outline-none min-h-[300px] px-4 py-3",
      },
    },
    onUpdate: ({ editor: e }) => {
      onChange(e.getHTML());
    },
  });

  // Sync external content changes (e.g., when accepting an AI candidate)
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content, { emitUpdate: false });
    }
  }, [content, editor]);

  const insertAtCursor = useCallback(
    (text: string) => {
      editor?.chain().focus().insertContent(text).run();
    },
    [editor],
  );

  return (
    <div className="border border-gray-200 rounded-lg bg-white">
      {/* Minimal toolbar */}
      {editor && editable && (
        <div className="flex items-center gap-1 px-3 py-2 border-b border-gray-100">
          <ToolbarButton
            active={editor.isActive("bold")}
            onClick={() => editor.chain().focus().toggleBold().run()}
            label="B"
            className="font-bold"
          />
          <ToolbarButton
            active={editor.isActive("italic")}
            onClick={() => editor.chain().focus().toggleItalic().run()}
            label="I"
            className="italic"
          />
          <ToolbarButton
            active={editor.isActive("bulletList")}
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            label="•"
          />
          <ToolbarButton
            active={editor.isActive("orderedList")}
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            label="1."
          />
        </div>
      )}
      <EditorContent editor={editor} />
    </div>
  );
}

function ToolbarButton({
  active,
  onClick,
  label,
  className = "",
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        px-2 py-1 text-sm rounded transition-colors
        ${active ? "bg-gray-200 text-gray-900" : "text-gray-500 hover:bg-gray-100"}
        ${className}
      `}
    >
      {label}
    </button>
  );
}

// Re-export for use in step pages that need programmatic insertion
export type { EditorProps };
