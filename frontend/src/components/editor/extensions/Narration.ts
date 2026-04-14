import { Node, mergeAttributes } from "@tiptap/core";

/**
 * 旁白块 — 时间/空间过渡、叙事说明
 * 示例：三年后的夏天——
 */
export const Narration = Node.create({
  name: "narration",
  group: "block",
  content: "inline*",
  defining: true,

  parseHTML() {
    return [{ tag: 'div[data-type="narration"]' }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      mergeAttributes(HTMLAttributes, { "data-type": "narration" }),
      0,
    ];
  },
});
