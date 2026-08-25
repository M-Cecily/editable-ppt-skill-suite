# Evidence-linked content review

## Scope

Use the target PPTX/image and user-uploaded papers, guidelines, reports, or reference documents. External search is opt-in. Review does not edit the deck by default.

## Inventories

Extract slide titles, claims, numbers/units, thresholds, causal language, mechanisms, diagnostic/treatment/prognostic statements, chart conclusions, abbreviations, arrow relationships, limitations, and source notes. Resolve stable `object_id` values from reconstruction or inspection.

For each source record filename, title, document type, year, identifiers only when present, page count, and usable locator scheme.

## Relevance and use

Classify each source as `direct`, `partial`, `background`, `weak`, or `unrelated`. Record affected slides/objects/topics, supported and conflicting claims, additions, exclusions, and evidence limits.

Assign one or more actions: `support_existing`, `citation_only`, `supplement_content`, `correct_content`, `restructure`, `replace_visual_logic`, `background_only`, `do_not_use`. Unrelated or weak sources must not be forced into the deck.

## Evidence matrix

Every actionable row includes:

`suggestion_id, slide_no, object_id, original_claim, issue_type, evidence_status, evidence_strength, supporting_source, source_locator, conflicting_source, recommended_action, recommended_text, rationale, confidence`.

Evidence status: `supported`, `partially_supported`, `unsupported`, `conflicting`, `outdated`, `unverifiable_from_uploaded_sources`, `not_applicable`.

Priority: `critical`, `high`, `medium`, `optional`.

Change type: `factual_correction`, `evidence_boundary`, `terminology`, `data_correction`, `narrative_restructure`, `visual_encoding`, `deletion`, `addition`, `simplification`, `citation_or_source_note`.

Source locators name the file and use available page, section, figure, table, paragraph, or anchor text. “根据文献” is not a locator.

## Required output

```text
review/content_review.md
review/evidence_matrix.csv
review/revision_plan.json
review/claim_inventory.csv
review/source_inventory.csv
review/review_summary.md
```

The concise user summary states overall relevance, recommended use, affected pages, protected pages, and that a structured plan was created. Stop after review unless iteration was explicitly requested.

