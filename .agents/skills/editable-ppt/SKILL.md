---
name: editable-ppt
description: Reconstruct uploaded images or PowerPoint files as object-editable PPTX, relate uploaded papers to the active deck, apply feedback in three distinct editable versions, compare revisions, or continue a prior A/B/C round. Use as the single conversational entry for editable-PPT work, including vague requests such as “处理这个”, “做成可编辑的”, “看一下这个论文”, “再来三个”, or “用 B 继续”.
---

# Editable PPT

This is the only public conversational entry. Keep the user at the level of files, intent, and visible outputs; route implementation through `$editable-ppt-pipeline` and its three explicit-only capabilities.

## Resolve the current request

1. Prefer files in the current message, then a user-named version, the active project's `active_version`, its `active_baseline`, and finally the only unfinished project in the workspace.
2. Do not ask for a path, filename, slide range, QA preference, or file already stored in project state.
3. If a first PPT/PPTX or supported page image arrives without an operation, perform only lightweight identification and ask exactly one choice question using the menu in [references/dialogue-routing.md](references/dialogue-routing.md).
4. Skip the menu when the message already means reconstruct, review, iterate, reject a round, select a version, or request comparisons.
5. A newly uploaded paper defaults to content review when an active PPT project exists. Without an active PPT, ask only for the target PPT.
6. A clear modification message after review is complete feedback: save it, merge it with the revision plan, and start a three-version round unless the user says they are not finished.
7. “三个都不满意/再来三个” starts a new round without asking why. Preserve rejection reasons when supplied and avoid the rejected design signatures.
8. “选 B/用 C 继续/保留 A” updates the active baseline or retained candidates from project state; do not require the user to remember filenames.

## Dispatch

- Reconstruct: invoke `$editable-ppt-reconstruct`.
- Review uploaded literature: invoke `$editable-ppt-content-review`.
- Generate or continue A/B/C versions: invoke `$editable-ppt-iterate`.
- Full or stateful work: invoke `$editable-ppt-pipeline`, whose CLI creates/resolves project state and returns the executable stage plan.

Do not treat the router CLI as the creative reconstruction or scientific reviewer. Execute each returned stage with the corresponding skill and record its real outputs back into state.

## Defaults and delivery

Process all slides, preserve aspect ratio and source language, retain the source visual language unless the user asks otherwise, never overwrite an input, run structural/visual/editability QA, render every output slide, and create comparisons automatically.

Keep replies concise: show the editable PPT or three candidate PPTX files, comparison entry points, and QA status. Keep manifests, CSV/JSON evidence, logs, and state files available but do not dump them into ordinary replies.
