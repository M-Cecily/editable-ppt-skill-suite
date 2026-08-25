#!/usr/bin/env python3
"""Audit PPTX package integrity, slide structure, and obvious editability risks."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def natural_key(value: str) -> list[object]:
    return [int(token) if token.isdigit() else token for token in re.split(r"(\d+)", value)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_xml(archive: zipfile.ZipFile, member: str) -> ET.Element:
    return ET.fromstring(archive.read(member))


def slide_size(archive: zipfile.ZipFile) -> tuple[int, int]:
    root = parse_xml(archive, "ppt/presentation.xml")
    size = root.find("p:sldSz", NS)
    if size is None:
        return 0, 0
    return int(size.get("cx", "0")), int(size.get("cy", "0"))


def picture_coverage(pic: ET.Element, width: int, height: int) -> float:
    xfrm = pic.find("p:spPr/a:xfrm", NS)
    if xfrm is None or width <= 0 or height <= 0:
        return 0.0
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    if off is None or ext is None:
        return 0.0
    x = int(off.get("x", "0"))
    y = int(off.get("y", "0"))
    cx = int(ext.get("cx", "0"))
    cy = int(ext.get("cy", "0"))
    inside_w = max(0, min(x + cx, width) - max(x, 0))
    inside_h = max(0, min(y + cy, height) - max(y, 0))
    return (inside_w * inside_h) / (width * height)


def relationship_issues(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    members = [name for name in archive.namelist() if name.endswith(".rels")]
    for member in members:
        try:
            root = parse_xml(archive, member)
        except (ET.ParseError, KeyError):
            issues.append(
                {
                    "slide": "",
                    "object_type": "relationship_part",
                    "severity": "error",
                    "object_id": member,
                    "details": "Relationship XML cannot be parsed",
                }
            )
            continue
        for rel in root.findall("pr:Relationship", NS):
            if rel.get("TargetMode") == "External":
                slide_match = re.search(r"slide(\d+)\.xml\.rels$", member)
                issues.append(
                    {
                        "slide": slide_match.group(1) if slide_match else "",
                        "object_type": "external_relationship",
                        "severity": "error",
                        "object_id": rel.get("Id", ""),
                        "details": rel.get("Target", ""),
                    }
                )
    return issues


def audit(deck: Path, output: Path) -> tuple[dict[str, Any], int]:
    output.mkdir(parents=True, exist_ok=True)
    unresolved: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    package_errors: list[str] = []

    if not deck.exists():
        package_errors.append("FILE_NOT_FOUND")
    elif not zipfile.is_zipfile(deck):
        package_errors.append("NOT_AN_OPENXML_ZIP_PACKAGE")

    if package_errors:
        summary = {
            "schema_version": 1,
            "deck": str(deck),
            "package_valid": False,
            "package_errors": package_errors,
            "slide_count": 0,
            "pass": False,
        }
        (output / "structure_audit.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        write_csv(
            output / "editability_audit.csv",
            ["slide", "text_shapes", "shape_objects", "pictures", "native_charts", "native_tables", "full_slide_pictures", "editable_object_ratio", "status"],
            [],
        )
        write_csv(
            output / "unresolved_objects.csv",
            ["slide", "object_type", "severity", "object_id", "details"],
            [],
        )
        return summary, 2

    with zipfile.ZipFile(deck) as archive:
        bad_member = archive.testzip()
        if bad_member:
            package_errors.append(f"CRC_ERROR:{bad_member}")
        try:
            width, height = slide_size(archive)
        except (KeyError, ET.ParseError, ValueError) as exc:
            width, height = 0, 0
            package_errors.append(f"PRESENTATION_XML_ERROR:{exc}")

        slide_members = sorted(
            (
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            ),
            key=natural_key,
        )
        unresolved.extend(relationship_issues(archive))

        for slide_index, member in enumerate(slide_members, start=1):
            try:
                root = parse_xml(archive, member)
            except (KeyError, ET.ParseError) as exc:
                unresolved.append(
                    {
                        "slide": slide_index,
                        "object_type": "slide_xml",
                        "severity": "error",
                        "object_id": member,
                        "details": str(exc),
                    }
                )
                continue

            shapes = root.findall(".//p:sp", NS)
            connectors = root.findall(".//p:cxnSp", NS)
            pictures = root.findall(".//p:pic", NS)
            graphic_frames = root.findall(".//p:graphicFrame", NS)
            text_shapes = sum(1 for shape in shapes if shape.findall(".//a:t", NS))
            native_charts = 0
            native_tables = 0
            for frame in graphic_frames:
                data = frame.find(".//a:graphicData", NS)
                uri = data.get("uri", "") if data is not None else ""
                native_charts += int("chart" in uri.lower())
                native_tables += int("table" in uri.lower())

            full_slide = []
            for picture_index, picture in enumerate(pictures, start=1):
                coverage = picture_coverage(picture, width, height)
                if coverage >= 0.90:
                    full_slide.append((picture_index, coverage))
                    unresolved.append(
                        {
                            "slide": slide_index,
                            "object_type": "full_slide_picture",
                            "severity": "error",
                            "object_id": f"picture_{picture_index}",
                            "details": f"Covers {coverage:.1%} of slide; likely flattened page",
                        }
                    )

            editable_objects = len(shapes) + len(connectors) + native_charts + native_tables
            total_objects = editable_objects + len(pictures)
            ratio = editable_objects / total_objects if total_objects else 0.0
            status = "pass"
            if full_slide:
                status = "fail_flattened"
            elif total_objects == 0:
                status = "warning_empty"
                unresolved.append(
                    {
                        "slide": slide_index,
                        "object_type": "empty_slide",
                        "severity": "warning",
                        "object_id": "",
                        "details": "No shapes, pictures, native charts, or native tables detected",
                    }
                )
            rows.append(
                {
                    "slide": slide_index,
                    "text_shapes": text_shapes,
                    "shape_objects": len(shapes) + len(connectors),
                    "pictures": len(pictures),
                    "native_charts": native_charts,
                    "native_tables": native_tables,
                    "full_slide_pictures": len(full_slide),
                    "editable_object_ratio": f"{ratio:.4f}",
                    "status": status,
                }
            )

    error_count = sum(1 for item in unresolved if item.get("severity") == "error")
    warning_count = sum(1 for item in unresolved if item.get("severity") == "warning")
    slide_count = len(rows)
    passed = not package_errors and slide_count > 0 and error_count == 0
    summary = {
        "schema_version": 1,
        "deck": str(deck.resolve()),
        "package_valid": not package_errors,
        "package_errors": package_errors,
        "slide_size_emu": {"width": width, "height": height},
        "slide_count": slide_count,
        "totals": {
            "text_shapes": sum(int(row["text_shapes"]) for row in rows),
            "shape_objects": sum(int(row["shape_objects"]) for row in rows),
            "pictures": sum(int(row["pictures"]) for row in rows),
            "native_charts": sum(int(row["native_charts"]) for row in rows),
            "native_tables": sum(int(row["native_tables"]) for row in rows),
            "full_slide_pictures": sum(int(row["full_slide_pictures"]) for row in rows),
        },
        "unresolved_error_count": error_count,
        "unresolved_warning_count": warning_count,
        "pass": passed,
        "interpretation": (
            "Raster pictures are permitted for image-only content; a picture covering at least 90% of a slide is treated as a flattened-page failure."
        ),
    }

    write_csv(
        output / "editability_audit.csv",
        ["slide", "text_shapes", "shape_objects", "pictures", "native_charts", "native_tables", "full_slide_pictures", "editable_object_ratio", "status"],
        rows,
    )
    write_csv(
        output / "unresolved_objects.csv",
        ["slide", "object_type", "severity", "object_id", "details"],
        unresolved,
    )
    (output / "structure_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary, 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck")
    parser.add_argument("--output", required=True)
    parser.add_argument("--strict", action="store_true", help="Return non-zero if a flattened slide, invalid package, or external relationship is found")
    args = parser.parse_args()
    summary, result = audit(Path(args.deck).expanduser().resolve(), Path(args.output).expanduser().resolve())
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.strict:
        return result
    return 0 if result != 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())
