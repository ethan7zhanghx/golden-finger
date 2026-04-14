import { Node, mergeAttributes } from "@tiptap/core";

/**
 * 对白块 — 人物台词
 * 格式：人物名：台词内容
 * Enter 键后继续对白，Tab 键切换到动作描写
 */
export const Dialogue = Node.create({
  name: "dialogue",
  group: "block",
  content: "inline*",
  defining: true,

  parseHTML() {
    return [{ tag: 'div[data-type="dialogue"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "dialogue" }),
      0,
    ];
  },

  addKeyboardShortcuts() {
    return {
      Tab: ({ editor }) => {
        const { $from } = editor.state.selection;
        if ($from.node().type.name !== this.name) return false;
        return editor.chain().setNode("action").run();
      },
    };
  },
});
