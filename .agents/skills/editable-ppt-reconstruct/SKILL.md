---
name: editable-ppt-reconstruct
description: Convert PPTX or verified page-image inputs into object-level editable PowerPoint by separating text, shapes, connectors, icons, tables, charts, and true image regions. Use explicitly for reconstruction, not ordinary slide copy editing or literature review.
---

# Editable PPT Reconstruct

Reconstruct the supplied pages without covering them with a screenshot or whole-page SVG. Use the existing PPTX structure first; enter visual reconstruction only for flattened slides or image inputs.

Before authoring, read [references/reconstruction.md](references/reconstruction.md). Also use the installed `presentations:Presentations` skill for every PPTX authoring operation and its required inspect/render/QA workflow.

Core invariants:

- Native text stays native text; preserve runs, line breaks, emphasis, alignment, and scientific notation.
- Basic geometry, lines, arrows, and connectors are independent PowerPoint objects.
- Tables and charts are native when source structure or confidently recovered data supports them; otherwise rebuild chart components as editable shapes and report uncertainty.
- Only actual photos, medical images, microscopy, complex textures, logos, or indivisible source artwork may remain raster. Crop those assets without embedded labels or arrows and record their source boxes.
- Give reconstructed objects stable `object_id` values and write the inventories described in the reference.
- Preserve source meaning and original files. Record substitutions, unresolved objects, and degradations instead of guessing.

Render and inspect every output slide. A page that can only be moved as one object is not object-level editable.
