# Object-level reconstruction procedure

## Input path

1. PPTX: inspect native text, shapes, images, groups, tables, charts, layouts, coordinates, and z-order. Do not OCR readable native text.
2. Flattened PPTX or image: render/normalize the page, infer page geometry, and reconstruct from visual evidence. OCR is allowed only for rasterized text and must be checked against the page.
3. Legacy or unverified format: convert only through a reliable available tool, preserve the source, and record the conversion. Otherwise stop as degraded/blocked.

Repository-golden-tested inputs are PPTX and BMP, with PNG/JPG assets. WEBP/TIFF and legacy PPT are not golden-tested.

## Page model

For every page record canvas, background, text hierarchy/style, shapes, connectors, icons, tables, charts, image regions, groups, occlusion, z-order, alignment, spacing, and repeated components. Assign stable IDs such as `s03_title_01`, `s03_chart_axis_x`, and `s03_image_histology_01`.

## Reconstruction priority

1. Text → native text boxes; preserve runs, line breaks, superscript/subscript, emphasis, color, alignment, and language.
2. Basic graphics → independent native shapes, lines, arrows, and connectors.
3. Icons/diagrams → independent logical objects. Use SVG only for an indivisible complex vector, never a whole page.
4. Tables → native tables with editable cell text when feasible.
5. Charts → native chart when underlying data exists; otherwise editable axes/marks/labels. Never guess hidden values.
6. True imagery → local raster crop with original resolution/transparency when possible; exclude all editable annotations.

Use the stable repository patterns listed in `/workflow_inventory.md`: artifact-tool import/inspect/export, template starter/fidelity helpers, Pillow edge-connected cutout, and rendered QA. Existing builders are fixture-specific and must not be run against unrelated files by changing only paths.

## Required output

```text
reconstruct/reconstructed_editable.pptx
reconstruct/source_manifest.json
reconstruct/object_inventory.csv
reconstruct/asset_manifest.csv
reconstruct/font_substitutions.csv
reconstruct/data_uncertainty_report.md
reconstruct/reconstruction_log.md
reconstruct/rendered_slides/
reconstruct/reconstruction_montage.png
```

`object_inventory.csv` includes `slide_no, object_id, object_type, source_bbox, output_bbox, reconstruction_method, editability_level, source_reference, confidence, warning`.

Allowed editability levels: `native_text`, `native_shape`, `native_table`, `native_chart`, `editable_vector`, `editable_shapes`, `raster_image`, `unresolved`.

## Prohibited shortcuts

No full-page screenshot background, whole-page SVG, rasterized text, merged all-page group, guessed chart data, unlogged asset replacement, silent scientific edits, or source overwrite.

