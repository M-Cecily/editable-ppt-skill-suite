# Stable CLI entry

The deterministic entry is:

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py `
  --mode reconstruct|review|iterate|full|auto `
  --source <file-or-directory> `
  --literature <file-or-directory> `
  --review-file <revision_plan.json> `
  --slide-range all `
  --output <directory> `
  --approval-policy interactive|auto `
  --target-language source|<language> `
  --fidelity-priority visual_exact|balanced|semantic_editability `
  --message "<natural-language request>"
```

`--source` and `--literature` are repeatable. Omit formal parameters when the natural-language message and active project state already resolve them.

The command creates or loads project state and prints a JSON dispatch plan. It does not perform model-dependent reconstruction or scientific judgment. Execute `stages` with the named Skills, then record actual outputs:

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py --record-reconstruction <pptx>
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py --record-review <revision_plan.json>
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py --record-version A=<pptx> --record-version B=<pptx> --record-version C=<pptx>
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py --comparison <image-or-directory>
python .agents/skills/editable-ppt-pipeline/scripts/editable_ppt.py --record-design-signatures <design_signatures.json>
```

Useful state actions:

```powershell
python .../editable_ppt.py --message "三个都不满意，再来三个"
python .../editable_ppt.py --message "用 B 继续，第四页重新做"
python .../editable_ppt.py --message "回到原版"
```

Exit code `0` means a usable plan or completed state update. Exit code `2` means an irreplaceable input is missing. The JSON `status` remains authoritative.

Comparison generation:

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/compare_rendered.py `
  --before <render-dir> --a <render-dir> --b <render-dir> --c <render-dir> `
  --output <comparisons-dir> --round 1
```

PPTX package/editability audit:

```powershell
python .agents/skills/editable-ppt-pipeline/scripts/audit_pptx.py <deck.pptx> --output <qa-dir> --strict
```
