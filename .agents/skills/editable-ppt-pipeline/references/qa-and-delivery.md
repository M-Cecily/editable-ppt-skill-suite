# QA and delivery gate

Do not record a PPTX as completed until all applicable gates pass.

## Package and structure

- PPTX opens and contains the expected slide count and size.
- No broken ZIP members, external media references, blank accidental slides, empty inherited placeholders, or non-intentional off-canvas objects.
- Render every exported slide from the final PPTX; do not rely only on in-memory previews.
- Run `slides_test.py` and template-fidelity validation when a source template/starter is used.

## Editability

- Audit native text, shapes/connectors, tables, charts, images, and unresolved objects per slide.
- Reject a whole-slide screenshot or whole-slide SVG used as a false editable layer.
- Raster images contain only true image content; labels, axes, arrows, and legends remain editable.
- Native-chart versus editable-shapes status reflects the actual PPTX objects.

Use `scripts/audit_pptx.py` to create `editability_audit.csv`, `structure_audit.json`, and `unresolved_objects.csv`. It is a package-level gate, not a substitute for visual inspection.

## Visual and evidence

- Inspect every slide for crop, font, alignment, wrapping, overlap, z-order, and connector errors.
- Create baseline/A/B/C comparisons with `scripts/compare_rendered.py` for every iteration round.
- For reviewed decks, every added fact and applied change traces to uploaded evidence or explicit user feedback. Critical findings cannot disappear silently.

## User-facing delivery

Show only final PPTX files, comparison entry points, short version summaries, and QA status. Keep detailed manifests and logs available in the project directory.

