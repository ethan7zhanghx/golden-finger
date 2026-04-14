import { Node, mergeAttributes } from "@tiptap/core";

/**
 * 场景头块 — 每集/场景的开头标识
 * 示例：第一集 · 咖啡厅
 * Enter 键后自动切换到动作描写块
 */
export const SceneHeading = Node.create({
  name: "sceneHeading",
  group: "block",
  content: "inline*",
  defining: true,

  parseHTML() {
    return [{ tag: 'div[data-type="scene-heading"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "scene-heading" }),
      0,
    ];
  },

  addKeyboardShortcuts() {
    return {
      Enter: ({ editor }) => {
        const { $from } = editor.state.selection;
        if ($from.node().type.name !== this.name) return false;
        return editor.chain().splitBlock().setNode("action").run();
      },
    };
  },
});
