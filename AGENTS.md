# Editable PPT project rules

- Route requests to reconstruct image/PPT pages, review a deck against literature, generate A/B/C variants, or continue an earlier deck iteration through `$editable-ppt`.
- Never overwrite a user's source file. Write reconstructed decks, reviews, variants, renders, comparisons, and QA records to project-scoped output directories.
- Before delivery, validate package structure, editable-object structure, rendered appearance, overflow, and comparison outputs. Report warnings truthfully; do not claim an image-only region is editable.
- In the user-facing result, link the actual PPTX and comparison outputs and state whether structural, visual, and editability checks passed.

