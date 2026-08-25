# Project state and baseline selection

Projects live under `projects/<project_id>/`; `.editable-ppt/active_project.json` stores only the active project pointer.

`project_state.json` records at least:

```json
{
  "project_id": "",
  "project_name": "",
  "source_files": [],
  "original_source": "",
  "reconstructed_baseline": "",
  "active_baseline": "",
  "active_version": "",
  "literature_files": [],
  "latest_review": "",
  "latest_revision_plan": "",
  "user_feedback_history": [],
  "pending_feedback": [],
  "iteration_round": 0,
  "generated_versions": [],
  "selected_versions": [],
  "retained_versions": [],
  "rejected_versions": [],
  "design_signature_files": [],
  "comparison_outputs": [],
  "last_updated": ""
}
```

## Project resolution

Choose: new source in current message → explicitly named version → active version → active baseline → only unfinished project. Ask only if multiple projects remain equally plausible.

## Baselines

- Reconstruction completion sets `reconstructed_baseline`, `active_baseline`, and `active_version` to the new editable deck.
- Selecting a version appends to `selected_versions` and sets that version as `active_version` and `active_baseline`.
- “回到原版” resets `active_baseline` and `active_version` to `reconstructed_baseline`; history remains.
- Comparison baseline: user choice → selected version → active baseline → reconstructed baseline → original source.
- If all candidates are rejected and none selected, compare the next round to `reconstructed_baseline`.

## Rounds

Each `round_XX` keeps A/B/C outputs, rendered pages, comparisons, `change_summary.md`, `design_signatures.json`, and `round_state.json`. Rejected versions are immutable history. A new round must differ from rejected design signatures on a majority of layout strategy, narrative strategy, visual grammar, chart strategy, density, and reading path.
