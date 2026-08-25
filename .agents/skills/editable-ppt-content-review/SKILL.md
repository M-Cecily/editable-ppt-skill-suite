---
name: editable-ppt-content-review
description: Review PPT or image-based presentation claims against user-uploaded papers, guidelines, and reference documents, producing evidence-linked findings and a machine-readable revision plan without modifying the deck by default. Use explicitly when both a target deck and literature are available.
---

# Editable PPT Content Review

Review the active deck against the uploaded sources. Do not modify the PPTX unless the user separately authorizes iteration.

Read [references/content-review.md](references/content-review.md) and validate the output against [references/revision-plan.schema.json](references/revision-plan.schema.json).

Use only user-provided sources unless the user explicitly asks for external research. Do not invent citations, locators, data, DOI values, or evidence. For every paper classify relevance (`direct`, `partial`, `background`, `weak`, or `unrelated`) and one or more permitted uses (`support_existing`, `citation_only`, `supplement_content`, `correct_content`, `restructure`, `replace_visual_logic`, `background_only`, `do_not_use`).

Create a claim inventory before judging the deck. Tie every actionable finding to a stable slide/object ID, evidence status, source locator, priority, change type, rationale, and confidence. Conflicting or unverifiable evidence remains explicit; do not silently choose a side.

Write the complete review artifact set and a concise user-facing summary. By default, stop after review and wait for feedback or an explicit request to generate versions.
