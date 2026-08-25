# Editable PPT Skill Suite

一套面向 Codex 的可编辑 PowerPoint 工作流 Skill Suite，用于把整页图片或扁平化 PPT 重构为对象级可编辑 PPTX，并支持结合论文进行内容审查、生成 A/B/C 三个差异化版本以及跨轮次持续迭代。

本仓库只包含 Skill、确定性辅助脚本和状态路由测试，不包含任何用户 PPT、论文、图片、项目状态或本地生成结果。

## 核心能力

- 将 PPTX、BMP、PNG、JPG 等输入拆解为可编辑文字、形状、连接线、箭头、图标、表格和图表组件。
- 将真实照片、医学影像、显微图、复杂纹理等不可合理拆分的区域单独裁切后作为图片素材保留。
- 将上传的论文、指南或报告与当前 PPT 自动关联，输出证据矩阵和机器可读的 `revision_plan.json`。
- 根据审查意见或用户反馈生成三个对象级可编辑版本：保守修正版、结构优化版和出版级重设计版。
- 保存活动项目、基线版本、反馈、A/B/C 选择、拒绝历史和迭代轮次。
- 每轮生成修改前与 A/B/C 的四栏总览、逐页对比图和版本 montage。
- 审计 PPTX 包结构、对象可编辑性、整页图片扁平化和外部依赖。

## Skill 架构

普通用户只需要使用 `$editable-ppt`。其余 Skill 是内部能力，默认不会自动触发。

| Skill | 调用策略 | 作用 |
|---|---|---|
| `editable-ppt` | 可自动触发 | 统一对话入口，理解自然语言并继承活动项目上下文 |
| `editable-ppt-pipeline` | 显式/内部 | 路由、项目状态、运行目录、阶段编排和 QA 闸门 |
| `editable-ppt-reconstruct` | 显式/内部 | 对象级 PPT 重构与图片区域分离 |
| `editable-ppt-content-review` | 显式/内部 | 文献相关性、证据审查和 revision plan |
| `editable-ppt-iterate` | 显式/内部 | A/B/C 三版本生成、比较、选择和多轮迭代 |

```text
.agents/skills/
├── editable-ppt/
├── editable-ppt-pipeline/
│   ├── scripts/editable_ppt.py
│   ├── scripts/audit_pptx.py
│   └── scripts/compare_rendered.py
├── editable-ppt-reconstruct/
├── editable-ppt-content-review/
└── editable-ppt-iterate/
```

## 安装

### 作为项目级 Skill 使用

克隆仓库后，在该仓库目录中启动 Codex。Skill 已位于 `.agents/skills/`，无需额外复制。

```powershell
git clone <your-repository-url>
cd editable-ppt-skill-suite
```

### 安装到其他项目

将本仓库的五个 Skill 目录复制到目标项目的 `.agents/skills/`：

```powershell
Copy-Item -Path ".agents\skills\editable-ppt*" `
  -Destination "<target-project>\.agents\skills" `
  -Recurse -Force
```

重新打开目标项目后，可显式输入 `$editable-ppt`，也可以直接使用“把这个做成可编辑 PPT”“看一下这个论文”“按意见做三个版本”等自然语言。

## 使用示例

### 1. 首次上传但意图不明确

系统只询问一次：

```text
1. 重构为各部分可编辑的 PPT
2. 用论文审查或优化这份 PPT 的内容
3. 根据修改意见生成三个修改版本
```

回复 `1`、`2`、`3`，或直接说“重构”“论文审查”“做三个版本”即可继续。

### 2. 可编辑重构

```text
把这张整页图片重构成各部分可编辑的 PPT，图表也拆开重绘，真实图片单独抠出来。
```

### 3. 上传论文后自动审查

当前项目已有 PPT 时，后续上传 PDF 默认关联当前 PPT，不需要重新指定文件：

```text
看看这篇论文和前面的 PPT 是否相关，需要补充或纠正什么。
```

每篇资料会被归类为 `direct`、`partial`、`background`、`weak` 或 `unrelated`，并给出支持、补充、纠正、重构或不使用建议。

### 4. 生成三个版本

```text
第二页压缩文字，第三页改成机制流程，保持原来的配色，给我做三个版本。
```

### 5. 连续迭代

```text
三个都不满意，再来三个。
用 B 继续，第四页重新做。
保留 A，另外两个重做。
回到原版。
输出前后对比。
```

拒绝一轮后不会强制询问原因。上一轮的设计签名会进入排除条件，下一轮不得只更换颜色或字体。

## 项目状态

运行时状态默认保存在使用者自己的工作区，不应提交到 Git：

```text
.editable-ppt/active_project.json
projects/<project_id>/project_state.json
```

状态会记录源文件、活动基线、当前版本、论文、审查计划、反馈、迭代轮次、A/B/C、选择/拒绝历史、设计签名和对比图路径。

## 确定性 CLI

路由器只解析意图和维护状态，不代替模型完成版式重构或科学判断。

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py `
  --mode auto `
  --source <pptx-or-image> `
  --literature <paper.pdf> `
  --message "做成可编辑的" `
  --workspace .
```

PPTX 包与可编辑性审计：

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/audit_pptx.py `
  <deck.pptx> --output <qa-directory> --strict
```

已渲染页面的四栏和逐页对比：

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/compare_rendered.py `
  --before <before-render-dir> `
  --a <a-render-dir> --b <b-render-dir> --c <c-render-dir> `
  --output <comparison-directory> --round 1
```

`compare_rendered.py` 需要 Pillow；其余两个脚本仅使用 Python 标准库。实际 PPTX 读取、编辑、渲染和导出依赖 Codex 工作区中的 `presentations:Presentations` Skill 与可用的演示文稿运行时。

## 输出约定

### 重构阶段

```text
reconstruct/
├── reconstructed_editable.pptx
├── object_inventory.csv
├── asset_manifest.csv
├── source_manifest.json
├── rendered_slides/
└── reconstruction_montage.png
```

### 内容审查阶段

```text
review/
├── content_review.md
├── evidence_matrix.csv
├── revision_plan.json
├── claim_inventory.csv
├── source_inventory.csv
└── review_summary.md
```

### 迭代阶段

```text
rounds/round_01/
├── version_a/version_a_editable.pptx
├── version_b/version_b_editable.pptx
├── version_c/version_c_editable.pptx
├── rendered/
├── comparisons/
├── change_summary.md
├── design_signatures.json
└── round_state.json
```

## 质量要求

交付前必须同时检查：

- PPTX ZIP/XML 包结构和预期页数；
- 文本、形状、连接线、图片、表格和图表对象结构；
- 是否用整页截图或整页 SVG 冒充可编辑页面；
- 每页最终导出渲染的裁切、字体、换行、重叠、层级和连接线；
- A/B/C 是否有实质布局与叙事差异；
- 论文新增事实是否可以追溯到用户上传的证据；
- 修改前、A、B、C 的总览和逐页对比是否齐全。

## 测试

仓库包含七个路由与状态端到端场景：

```powershell
python -m unittest tests.test_editable_ppt_router -v
```

覆盖首次单图上传、回复 `1`、重构后上传论文、发送修改意见、拒绝全部版本、带原因重做、选择 B 继续和重新进入活动项目。

## 隐私与安全

- 不覆盖源文件。
- 不把用户 PPT、论文、图片、状态文件、渲染结果或运行目录提交到仓库。
- 内容审查默认只使用用户上传的资料；没有证据时不得编造结论或引用。
- 图片区域会明确标记为栅格素材，不声称其像素内容可以编辑。
- 上传或调用外部服务前仍需获得相应授权。

## 已知限制

通用 OCR、语义版面分析、复杂背景分割和 PowerPoint 原生图表数据恢复仍依赖具体运行环境与模型判断。完整边界见 [LIMITATIONS.md](LIMITATIONS.md)。

