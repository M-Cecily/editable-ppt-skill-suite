---
name: editable-ppt-iterate
description: Apply a structured review plan and user feedback to an editable deck, generating conservative, structural, and redesigned object-editable versions with traceability, comparisons, round history, and rejection-aware continuation. Use explicitly when an editable baseline and executable review or feedback exist.
---

# Editable PPT Iterate

Read [references/iteration.md](references/iteration.md) before generating versions and validate design signatures with [references/design-signature.schema.json](references/design-signature.schema.json).

For the first round create three materially different editable PPTX files:

- A — conservative correction: preserve structure; apply factual, terminology, data, and evidence-boundary fixes.
- B — structural optimization: improve hierarchy, reading order, duplication, chart emphasis, and within-slide organization while retaining the main visual language.
- C — publication-grade redesign: rebuild layout and visual grammar where justified; split or merge slides only with content mapping and no unsupported conclusions.

Every applied change must trace to a `suggestion_id` or explicit user-feedback ID. Preserve unaffected scientific meaning and image identity. All text, shapes, icons, connectors, tables, and chart components remain object-editable under the reconstruction contract.

Every round renders all candidates, produces baseline comparisons, records QA, and writes design signatures. On rejection, keep history, store feedback, exclude the rejected strategies, and generate a new round without asking the user to re-upload inputs or explain rejection. Selection phrases update the active baseline as defined in the reference.
