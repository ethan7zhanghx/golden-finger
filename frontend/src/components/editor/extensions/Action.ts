import { Node, mergeAttributes } from "@tiptap/core";

/**
 * 动作描写块 — 场景中的行为/环境描写
 * Tab 键切换到对白块
 */
export const Action = Node.create({
  name: "action",
  group: "block",
  content: "inline*",
  defining: true,

  parseHTML() {
    return [{ tag: 'div[data-type="action"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "action" }),
      0,
    ];
  },

  addKeyboardShortcuts() {
    return {
      Tab: ({ editor }) => {
        const { $from } = editor.state.selection;
        if ($from.node().type.name !== this.name) return false;
        return editor.chain().setNode("dialogue").run();
      },
    };
  },
});
