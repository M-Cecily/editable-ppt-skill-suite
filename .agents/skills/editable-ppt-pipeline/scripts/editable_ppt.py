#!/usr/bin/env python3
"""Deterministic router and project-state manager for the editable PPT Skill Suite.

This script intentionally does not make creative or scientific decisions.  It turns
formal arguments, natural-language intent, and the active project into an auditable
dispatch plan that an agent can execute with the three capability Skills.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PRESENTATION_EXTENSIONS = {".ppt", ".pptx"}
PAGE_IMAGE_EXTENSIONS = {".bmp", ".png", ".jpg", ".jpeg"}
RECOGNIZED_IMAGE_EXTENSIONS = PAGE_IMAGE_EXTENSIONS | {".webp", ".tif", ".tiff"}
LITERATURE_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".ris", ".bib", ".nbib"}
VERSION_LABELS = ("A", "B", "C")

FIRST_UPLOAD_QUESTION = (
    "已识别当前文件。请选择：1）重构为各部分可编辑的 PPT；2）用论文审查或优化这份 PPT 的内容；"
    "3）根据修改意见生成三个修改版本。回复 1、2、3，或者直接说“重构”“论文审查”“做三个版本”？"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def canonical(path: str | Path, base: Path) -> str:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        return str(candidate.resolve())
    except OSError:
        return str(candidate.absolute())


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = os.path.normcase(os.path.normpath(item))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value, flags=re.UNICODE).strip("-_")
    return (cleaned or "editable-ppt-project")[:56]


def project_id_for(source_files: list[str]) -> str:
    primary = Path(source_files[0]) if source_files else Path("editable-ppt-project")
    digest = hashlib.sha1("\n".join(source_files).encode("utf-8")).hexdigest()[:8]
    return f"{slugify(primary.stem)}-{digest}"


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def default_state(project_id: str, source_files: list[str]) -> dict[str, Any]:
    primary = Path(source_files[0]).stem if source_files else project_id
    return {
        "schema_version": 1,
        "project_id": project_id,
        "project_name": primary,
        "source_files": source_files,
        "original_source": source_files[0] if source_files else "",
        "reconstructed_baseline": "",
        "active_baseline": "",
        "active_version": "",
        "literature_files": [],
        "latest_review": "",
        "latest_revision_plan": "",
        "user_feedback_history": [],
        "pending_feedback": [],
        "iteration_round": 0,
        "generated_versions": [],
        "selected_versions": [],
        "retained_versions": [],
        "rejected_versions": [],
        "design_signature_files": [],
        "comparison_outputs": [],
        "round_history": [],
        "last_dispatch": {},
        "created_at": now_iso(),
        "last_updated": now_iso(),
    }


def expand_inputs(values: list[str], workspace: Path, allowed: set[str]) -> list[str]:
    expanded: list[str] = []
    for raw in values:
        normalized = Path(canonical(raw, workspace))
        if normalized.is_dir():
            for child in sorted(normalized.rglob("*")):
                if child.is_file() and child.suffix.lower() in allowed:
                    expanded.append(str(child.resolve()))
        else:
            expanded.append(str(normalized))
    return unique(expanded)


def find_existing_project(workspace: Path, source_files: list[str]) -> str | None:
    projects = workspace / "projects"
    if not projects.exists() or not source_files:
        return None
    wanted = {os.path.normcase(os.path.normpath(item)) for item in source_files}
    for state_path in projects.glob("*/project_state.json"):
        state = read_json(state_path)
        if not state:
            continue
        known = {
            os.path.normcase(os.path.normpath(item))
            for item in state.get("source_files", [])
            if isinstance(item, str)
        }
        if wanted and wanted.issubset(known):
            return str(state.get("project_id") or state_path.parent.name)
    return None


def resolve_project(
    workspace: Path, project_id: str | None, source_files: list[str]
) -> tuple[str | None, dict[str, Any] | None, Path | None, bool]:
    active_path = workspace / ".editable-ppt" / "active_project.json"
    new_project = False
    resolved_id = project_id

    if not resolved_id and source_files:
        resolved_id = find_existing_project(workspace, source_files)
        if not resolved_id:
            resolved_id = project_id_for(source_files)
            new_project = True

    if not resolved_id:
        active = read_json(active_path) or {}
        resolved_id = active.get("project_id")

    if not resolved_id:
        candidates = sorted((workspace / "projects").glob("*/project_state.json"))
        if len(candidates) == 1:
            resolved_id = candidates[0].parent.name

    if not resolved_id:
        return None, None, None, False

    state_path = workspace / "projects" / resolved_id / "project_state.json"
    state = read_json(state_path)
    if state is None:
        state = default_state(resolved_id, source_files)
        new_project = True
    elif source_files:
        state["source_files"] = unique([*state.get("source_files", []), *source_files])
        state["original_source"] = state.get("original_source") or source_files[0]

    atomic_json(
        active_path,
        {
            "schema_version": 1,
            "project_id": resolved_id,
            "project_state": str(state_path.resolve()),
            "last_updated": now_iso(),
        },
    )
    return resolved_id, state, state_path, new_project


def contains_any(message: str, phrases: Iterable[str]) -> bool:
    lowered = message.lower()
    return any(phrase.lower() in lowered for phrase in phrases)


def infer_intent(message: str, source_files: list[str], literature_files: list[str]) -> str | None:
    stripped = message.strip()
    if stripped == "1":
        return "reconstruct"
    if stripped == "2":
        return "review"
    if stripped == "3":
        return "iterate"
    if contains_any(message, ("全流程", "完整流程", "从重构到审查", "full pipeline")):
        return "full"
    if contains_any(message, ("输出前后对比", "前后对比", "显示对比", "比较一下", "comparison")):
        return "compare"
    if contains_any(
        message,
        ("三个都不满意", "都不满意", "再来三个", "下一轮", "用 a 继续", "用 b 继续", "用 c 继续", "版本", "方案", "迭代", "调整", "修改", "改成", "重新做", "压缩文字", "加入论文", "按我的意见", "按这些意见", "说完了", "按这些生成", "现在生成"),
    ):
        return "iterate"
    if contains_any(message, ("内容审查", "审查", "结合论文", "核对论文", "review", "证据", "文献", "是否相关", "能不能用", "看看需要补什么")):
        return "review"
    if contains_any(message, ("重构", "可编辑", "拆分", "重绘", "抠图", "editable", "reconstruct")):
        return "reconstruct"
    if source_files and literature_files:
        return "full"
    if literature_files:
        return "review"
    return None


def latest_round_versions(state: dict[str, Any]) -> list[dict[str, Any]]:
    records = [item for item in state.get("generated_versions", []) if isinstance(item, dict)]
    if not records:
        return []
    round_number = max(int(item.get("round", 0)) for item in records)
    return [item for item in records if int(item.get("round", 0)) == round_number]


def find_version(state: dict[str, Any], label: str) -> dict[str, Any] | None:
    candidates = [
        item
        for item in state.get("generated_versions", [])
        if isinstance(item, dict) and str(item.get("label", "")).upper() == label.upper()
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: int(item.get("round", 0)))[-1]


def requested_selection(message: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit.upper()
    match = re.search(r"(?:用|选|选择|继续用)\s*([ABC])(?:\s|版|方案|继续|$)", message, flags=re.I)
    return match.group(1).upper() if match else None


def requested_retention(message: str) -> list[str]:
    return sorted(set(value.upper() for value in re.findall(r"保留\s*([ABC])", message, flags=re.I)))


def focus_slides(message: str) -> list[int]:
    result = [int(value) for value in re.findall(r"第\s*(\d+)\s*页", message)]
    chinese = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    for value in re.findall(r"第\s*([一二三四五六七八九十])\s*页", message):
        result.append(chinese[value])
    return sorted(set(result))


def rejection_constraints(message: str) -> list[dict[str, str]]:
    constraints: list[dict[str, str]] = []
    if contains_any(message, ("拥挤", "字太多", "文字太多", "密度太高")):
        constraints.append({"action": "reduce_density", "source": message})
    if re.search(r"B.{0,8}(逻辑|结构).{0,8}(可以|保留|不错)", message, flags=re.I):
        constraints.append({"action": "preserve_B_narrative_logic", "source": message})
    if contains_any(message, ("图太小", "图形太小", "图片太小")):
        constraints.append({"action": "enlarge_core_visuals", "source": message})
    if contains_any(message, ("太激进", "改动太大", "变化太大")):
        constraints.append({"action": "limit_structural_change", "source": message})
    return constraints


def add_feedback(state: dict[str, Any], message: str, kind: str = "feedback") -> None:
    if not message.strip():
        return
    state.setdefault("user_feedback_history", []).append(
        {"at": now_iso(), "kind": kind, "text": message.strip()}
    )


def parse_version_records(values: list[str], workspace: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for value in values:
        if "=" not in value:
            raise ValueError(f"版本记录必须使用 A=<pptx> 格式：{value}")
        label, path = value.split("=", 1)
        label = label.strip().upper()
        if label not in VERSION_LABELS:
            raise ValueError(f"版本标签仅支持 A/B/C：{label}")
        records.append((label, canonical(path.strip(), workspace)))
    return records


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("auto", "reconstruct", "review", "iterate", "full"), default="auto")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--literature", action="append", default=[])
    parser.add_argument("--review-file")
    parser.add_argument("--slide-range", default="all")
    parser.add_argument("--output")
    parser.add_argument("--approval-policy", choices=("interactive", "auto"), default="interactive")
    parser.add_argument("--target-language", default="source")
    parser.add_argument("--fidelity-priority", choices=("visual_exact", "balanced", "semantic_editability"), default="balanced")
    parser.add_argument("--message", default="")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--project-id")
    parser.add_argument("--new-round", action="store_true")
    parser.add_argument("--select", choices=VERSION_LABELS)
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--record-reconstruction")
    parser.add_argument("--record-review")
    parser.add_argument("--record-version", action="append", default=[])
    parser.add_argument("--comparison", action="append", default=[])
    parser.add_argument("--record-design-signatures", action="append", default=[])
    return parser


def dispatch(argv: list[str] | None = None) -> tuple[dict[str, Any], int]:
    args = make_parser().parse_args(argv)
    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    source_allowed = PRESENTATION_EXTENSIONS | RECOGNIZED_IMAGE_EXTENSIONS
    source_files = expand_inputs(args.source, workspace, source_allowed)
    literature_files = expand_inputs(args.literature, workspace, LITERATURE_EXTENSIONS)
    project_id, state, state_path, new_project = resolve_project(
        workspace, args.project_id, source_files
    )

    if state is None or state_path is None or project_id is None:
        result = {
            "status": "blocked",
            "reason": "NO_ACTIVE_PROJECT",
            "question": "请先提供要处理的 PPT、整页图片或项目 ID。",
            "stages": [],
        }
        return result, 2

    state["literature_files"] = unique([*state.get("literature_files", []), *literature_files])
    project_root = state_path.parent
    run_stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(canonical(args.output, workspace)) if args.output else project_root / "runs" / run_stamp
    output_dir.mkdir(parents=True, exist_ok=True)

    events: list[str] = []
    if args.record_reconstruction:
        deck = canonical(args.record_reconstruction, workspace)
        state["reconstructed_baseline"] = deck
        state["active_baseline"] = deck
        state["active_version"] = deck
        events.append("recorded_reconstruction")

    if args.record_review:
        review = canonical(args.record_review, workspace)
        state["latest_review"] = str(Path(review).parent)
        state["latest_revision_plan"] = review
        events.append("recorded_review")

    try:
        version_records = parse_version_records(args.record_version, workspace)
    except ValueError as exc:
        return {"status": "blocked", "reason": "INVALID_VERSION_RECORD", "message": str(exc), "stages": []}, 2

    if version_records:
        round_number = max(1, int(state.get("iteration_round", 0)))
        state["iteration_round"] = round_number
        existing = state.setdefault("generated_versions", [])
        for label, path in version_records:
            existing.append(
                {
                    "label": label,
                    "path": path,
                    "round": round_number,
                    "status": "candidate",
                    "created_at": now_iso(),
                }
            )
        events.append("recorded_versions")

    for comparison in args.comparison:
        state.setdefault("comparison_outputs", []).append(
            {"path": canonical(comparison, workspace), "round": int(state.get("iteration_round", 0)), "created_at": now_iso()}
        )
    if args.comparison:
        events.append("recorded_comparisons")

    for signature_file in args.record_design_signatures:
        state.setdefault("design_signature_files", []).append(
            {"path": canonical(signature_file, workspace), "round": int(state.get("iteration_round", 0)), "created_at": now_iso()}
        )
    if args.record_design_signatures:
        events.append("recorded_design_signatures")

    message = args.message.strip()
    if args.review_file:
        state["latest_revision_plan"] = canonical(args.review_file, workspace)
    if args.keep:
        add_feedback(state, "保留：" + "；".join(args.keep), kind="keep_constraints")

    if contains_any(message, ("先记住", "先记着", "暂时别改", "先不要改", "先记录", "我还没说完", "后面还有", "先不要生成")):
        state.setdefault("pending_feedback", []).append({"at": now_iso(), "text": message})
        add_feedback(state, message, kind="pending")
        events.append("saved_pending_feedback")

    if contains_any(message, ("说完了", "按这些生成", "现在生成")) and state.get("pending_feedback"):
        state["pending_feedback"] = []
        events.append("promoted_pending_feedback")

    if contains_any(message, ("回到原版", "回到基线", "恢复原版")):
        baseline = state.get("reconstructed_baseline") or state.get("original_source")
        state["active_baseline"] = baseline
        state["active_version"] = baseline
        add_feedback(state, message, kind="baseline_reset")
        events.append("reset_to_reconstructed_baseline")

    selection = requested_selection(message, args.select)
    if selection:
        selected = find_version(state, selection)
        if selected:
            state["active_version"] = selected["path"]
            state["active_baseline"] = selected["path"]
            state.setdefault("selected_versions", []).append(
                {**selected, "selected_at": now_iso()}
            )
            add_feedback(state, message or f"选择 {selection}", kind="selection")
            events.append(f"selected_{selection}")

    retained_labels = requested_retention(message)
    for label in retained_labels:
        retained = find_version(state, label)
        if retained:
            state.setdefault("retained_versions", []).append({**retained, "retained_at": now_iso()})
            events.append(f"retained_{label}")

    rejection = args.new_round or contains_any(
        message, ("三个都不满意", "都不满意", "再来三个", "下一轮")
    )
    if rejection:
        previous = latest_round_versions(state)
        rejected = state.setdefault("rejected_versions", [])
        rejected_paths = {item.get("path") for item in rejected if isinstance(item, dict)}
        for item in previous:
            if item.get("path") not in rejected_paths:
                rejected.append({**item, "rejected_at": now_iso(), "reason": message or "user_rejected_round"})
            item["status"] = "rejected"
        next_round = max(1, int(state.get("iteration_round", 0)) + 1)
        state["iteration_round"] = next_round
        state.setdefault("round_history", []).append(
            {
                "round": next_round,
                "status": "planned",
                "reason": "all_candidates_rejected",
                "must_avoid_prior_design_signatures": True,
                "minimum_strategy_dimensions_changed": 4,
                "color_only_change_forbidden": True,
                "next_round_constraints": rejection_constraints(message),
                "created_at": now_iso(),
            }
        )
        add_feedback(state, message or "开始下一轮", kind="round_rejection")
        events.append("started_next_round_without_question")

    formal_updates_only = bool(events) and not message and args.mode == "auto" and not source_files and not literature_files
    inferred = infer_intent(message, source_files, literature_files)
    mode = args.mode if args.mode != "auto" else inferred

    if rejection:
        mode = "iterate"
    elif selection and contains_any(message, ("继续", "修改", "调整")):
        mode = "iterate"

    if formal_updates_only:
        mode = None

    if new_project and source_files and args.mode == "auto" and inferred is None:
        status = "needs_single_choice"
        stages: list[str] = []
        question = FIRST_UPLOAD_QUESTION
    else:
        status = "ready"
        question = ""
        stages = []
        if mode == "reconstruct":
            stages = ["editable-ppt-reconstruct"]
        elif mode == "review":
            stages = ["editable-ppt-content-review"]
        elif mode == "iterate":
            if literature_files and not state.get("latest_revision_plan"):
                stages.append("editable-ppt-content-review")
            stages.append("editable-ppt-iterate")
        elif mode == "full":
            stages = ["editable-ppt-reconstruct"]
            if state.get("literature_files"):
                stages.append("editable-ppt-content-review")
                stages.append("editable-ppt-iterate")
            else:
                status = "partial_ready"
        elif mode == "compare":
            stages = []
        elif mode is None and formal_updates_only:
            status = "state_updated"
        elif mode is None:
            status = "needs_single_choice"
            question = FIRST_UPLOAD_QUESTION

    missing: list[str] = []
    active_deck = (
        state.get("active_version")
        or state.get("active_baseline")
        or state.get("reconstructed_baseline")
        or state.get("original_source")
    )
    if mode == "reconstruct" and not state.get("source_files"):
        missing.append("source_files")
    if mode == "review":
        if not active_deck:
            missing.append("active_deck")
        if not state.get("literature_files"):
            missing.append("literature_files")
    if mode == "iterate":
        if not (state.get("active_baseline") or state.get("reconstructed_baseline")):
            missing.append("editable_baseline")
        if not (state.get("latest_revision_plan") or message or state.get("pending_feedback")):
            missing.append("revision_plan_or_feedback")
    if mode == "compare" and not active_deck:
        missing.append("active_deck")

    exit_code = 0
    if missing:
        status = "blocked"
        stages = []
        question = "缺少继续执行所需输入：" + "、".join(missing) + "。"
        exit_code = 2

    if message and not contains_any(message, ("先记住", "暂时别改", "先不要改", "先记录")):
        add_feedback(state, message)

    state["last_updated"] = now_iso()
    plan = {
        "status": status,
        "mode": mode or "state-update",
        "resolved_mode": mode or "state-update",
        "project_id": project_id,
        "project_state": str(state_path.resolve()),
        "active_deck": active_deck,
        "source_files": state.get("source_files", []),
        "literature_files": state.get("literature_files", []),
        "slide_range": args.slide_range,
        "focus_slides": focus_slides(message),
        "output": str(output_dir.resolve()),
        "approval_policy": args.approval_policy,
        "target_language": args.target_language,
        "fidelity_priority": args.fidelity_priority,
        "stages": stages,
        "iteration_round": int(state.get("iteration_round", 0)),
        "comparison_required": mode == "compare" or bool({"editable-ppt-reconstruct", "editable-ppt-iterate"}.intersection(stages)),
        "comparison_baseline": active_deck,
        "events": events,
        "missing": missing,
        "missing_inputs": missing,
        "retained_labels": retained_labels,
        "avoid_design_signature_files": [
            item.get("path")
            for item in state.get("design_signature_files", [])
            if isinstance(item, dict) and int(item.get("round", 0)) < int(state.get("iteration_round", 0))
        ],
        "question": question,
    }
    if status == "partial_ready" and mode == "full":
        plan["reason_code"] = "MISSING_LITERATURE"
        plan["deferred_missing"] = ["literature_files"]
        plan["note"] = "已可先重构；收到论文后自动进入内容审查和 A/B/C 迭代。"
    if mode == "compare":
        plan["comparison_action"] = "reuse_existing" if state.get("comparison_outputs") else "generate_from_stored_renders"

    state["last_dispatch"] = plan
    atomic_json(state_path, state)
    return plan, exit_code


def main(argv: list[str] | None = None) -> int:
    result, exit_code = dispatch(argv)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
