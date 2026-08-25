# Three-version and multi-round iteration

## Inputs and precedence

Require an object-editable baseline and `revision_plan.json` or explicit executable feedback. Priority: current user instruction → preserved/rejected directions → confirmed scientific correction → critical/high review → medium review → visual optimization. Ask once only when a request conflicts with evidence, requests unverifiable data, changes a key scientific conclusion, or contradicts another instruction.

## Round 1

- Version A: conservative correction; preserve layout and visual language.
- Version B: structural optimization; change hierarchy, reading order, duplication, chart emphasis, and internal layout.
- Version C: publication-grade redesign; change grid and visual grammar and, when justified, split/merge pages with content mapping.

The versions must differ materially on at least three of structure, hierarchy, reading path, visual grammar, chart encoding, density, split/merge strategy, and emphasis. Color/font-only variants do not qualify.

## Traceability and outputs

Every change links to a `suggestion_id` or `feedback_id`. Write A/B/C PPTX, change logs, object mapping, revision traceability, rendered pages, montages, and comparison summary. Use the pipeline comparison helper for four-column and page-level comparisons.

Round directory:

```text
rounds/round_01/
  version_a/version_a_editable.pptx
  version_b/version_b_editable.pptx
  version_c/version_c_editable.pptx
  rendered/
  comparisons/
  change_summary.md
  design_signatures.json
  round_state.json
```

## Rejection and continuation

- “三个都不满意/再来三个”: mark the prior candidates rejected, keep them, load their signatures, and choose three unused strategies. Do not ask for reasons.
- Rejection reasons become hard constraints for the next round.
- From round 2 create `previous_round_vs_current_round_overview.png` and a strategy-difference summary.
- “选 B/用 B 继续”: select B and set it as the next active baseline.
- “保留 B，重做 A 和 C”: keep B unchanged and generate two candidates only.
- “以 C 为基础，再做三个”: all new candidates use C as the content/structure baseline.
- “回到原版”: restore the reconstructed baseline without deleting history.

## Required QA

Render every candidate, run package/overflow/template checks, inspect every page, audit editability, and confirm critical evidence changes and user feedback are present. Do not deliver on first export if visible defects remain.

