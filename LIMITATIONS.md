# Current limitations

1. The repository contains strong PowerPoint import, object-editing, rendering, export, cutout, and QA examples, but several builders remain tied to the Danning gallbladder-polyp fixtures through hard-coded object IDs and coordinates. The Skill routes to and reuses them when applicable; it does not misrepresent them as a universal semantic parser.
2. Generic OCR, automatic semantic grouping, and general-purpose foreground extraction are not bundled here. Unsupported or visually ambiguous pages require agent judgment and may require a manual crop mask. WEBP/TIFF are recognized by the router but are not part of the currently verified real fixtures.
3. Image-only content may remain as a cropped raster asset. Text, shapes, tables, and chart elements around it must be rebuilt as editable objects, but the raster pixels themselves are not editable.
4. Existing chart rebuilds are usually editable PowerPoint shapes rather than native PowerPoint chart objects with an embedded workbook. The audit reports native charts separately so this distinction remains visible.
5. Scientific content review requires an accessible source paper or report. The current repository has no project-matched Danning trial paper fixture, so the scientific-review Skill and schema are validated structurally, not against a complete real literature-to-slide claim audit in this run.
6. The package audit detects invalid ZIP/XML packages, external relationships, and page-sized raster flattening. It cannot prove that every visual primitive is semantically correct; rendered comparison and human/agent visual inspection remain mandatory.
7. The comparison tool expects already rendered slide images. Rendering remains delegated to the stable presentation runtime documented in `workflow_inventory.md`.

