---
name: editable-ppt-pipeline
description: Orchestrate editable-PPT project state, mode routing, prerequisites, run directories, stage handoffs, comparison baselines, and final QA. Use explicitly for development, debugging, full reconstruct-review-iterate workflows, or resuming a stored project; ordinary users should use editable-ppt.
---

# Editable PPT Pipeline

Use the deterministic CLI to resolve inputs and project state, then execute the returned stages with the indicated sibling skills. The CLI is a router and state manager; it does not fabricate slides or scientific review results.

## Start or resume

Read [references/cli-usage.md](references/cli-usage.md), then run `scripts/editable_ppt.py` with the user-supplied files and message. Honor the plan's `resolved_mode`, `stages`, `missing_inputs`, `comparison_baseline`, and project directory. When a stage completes, call the CLI again with its record options so later turns can resume without re-uploading.

Mode prerequisites:

- `reconstruct`: at least one PPTX or supported page image.
- `review`: an active deck and user-provided literature. Do not invent a review if literature is missing.
- `iterate`: an object-editable deck plus a structured review plan or explicit executable feedback. If only literature is present, review first.
- `full`: reconstruct → review → iterate. Without literature, stop after reconstruction with `MISSING_LITERATURE` and a partial status.

## Orchestrate

1. Create a new run directory; never overwrite the source or earlier round.
2. Invoke `$editable-ppt-reconstruct`, `$editable-ppt-content-review`, and `$editable-ppt-iterate` only for their stage.
3. Preserve source and output hashes, assumptions, warnings, degradations, and actual tools used.
4. Use [references/project-state.md](references/project-state.md) for baseline selection, A/B/C selection, rejection, and round history.
5. Apply [references/qa-and-delivery.md](references/qa-and-delivery.md) before recording any PPTX as completed.
6. Record real output paths, review plans, versions, design signatures, and comparison artifacts in `project_state.json`.

Only ask when an irreplaceable input is missing, more than one project is equally plausible, or scientific evidence conflicts with a requested conclusion. Ask one focused question at a time.
