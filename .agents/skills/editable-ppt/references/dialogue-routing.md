# Conversational routing

## First upload with no clear intent

Perform lightweight file identification only. Reply with one menu and no other question:

```text
已识别：
- 文件：<文件名>
- 类型：<PPT / 图片>
- 页面：<页数或图片数>

请选择这次要做的操作：

1. 重构为各部分可编辑的 PPT
2. 用论文审查或优化这份 PPT 的内容
3. 根据修改意见生成三个修改版本

回复 1、2、3，或者直接说“重构”“论文审查”“做三个版本”。
```

If prerequisites are missing, annotate the same menu briefly; do not ask follow-up parameters.

## Intent map

- `1`, 重构, 做成可编辑的, 拆开重画, 图片转 PPT, 抠图重构 → reconstruct.
- `2`, 论文审查, 是否相关, 这个论文能不能用, 根据论文优化/调整结构 → review.
- `3`, 做三个版本, 按这些意见改, 生成三版, 应用修改意见 → iterate.
- 都不满意, 再来三个, 换三个方向, 继续出三版 → new iterate round.
- 选 A/B/C → select that candidate.
- 用 A/B/C 继续 → select candidate and set it as `active_baseline`.
- 保留 B，重做 A 和 C → retain B; generate only A and C replacements.
- 回到原版 → restore `reconstructed_baseline` without deleting history.
- 输出前后对比 → reuse stored renders; do not regenerate slides unnecessarily.

## Feedback semantics

A clear modification message after review is executable feedback. Start iteration automatically. If the user says 先记着, 我还没说完, 先不要生成, or 后面还有, store it in `pending_feedback` and wait. “说完了/按这些生成” promotes pending feedback into the next round.

Ask only for an irreplaceable missing input, an ambiguous active project, or a material scientific conflict. Ask one question at a time.

