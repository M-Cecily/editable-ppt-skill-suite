#!/usr/bin/env python3
"""Create deterministic before/A/B/C comparison boards from rendered slide images."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont, ImageOps


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
BG = "#eef1f4"
PANEL = "#ffffff"
INK = "#14213d"
MUTED = "#6b7280"
ACCENT = "#ef6c00"


def natural_key(path: Path) -> list[object]:
    return [int(token) if token.isdigit() else token.lower() for token in re.split(r"(\d+)", path.name)]


def images_at(path: Path) -> list[Path]:
    if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = sorted(
        (item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS),
        key=natural_key,
    )
    page_files = [item for item in files if re.search(r"(?:slide|page)[-_ ]?\d+", item.stem, flags=re.I)]
    return page_files or files


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return image.convert("RGB")


def fit_panel(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    fitted = ImageOps.contain(image, size, method=Image.Resampling.LANCZOS)
    panel = Image.new("RGB", size, PANEL)
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    panel.paste(fitted, (x, y))
    return panel


def safe_image(items: list[Path], index: int, fallback_size: tuple[int, int]) -> Image.Image:
    if index < len(items):
        return load_rgb(items[index])
    missing = Image.new("RGB", fallback_size, "#f8fafc")
    draw = ImageDraw.Draw(missing)
    draw.text((24, 24), "MISSING PAGE", fill="#b91c1c", font=font(26, bold=True))
    return missing


def make_overview(
    sets: list[tuple[str, list[Path]]], output: Path, round_number: int
) -> None:
    page_count = max((len(items) for _, items in sets), default=0)
    if page_count == 0:
        raise ValueError("No rendered images found")

    cell_w, cell_h = 420, 250
    gap, margin, header_h, row_label_w = 20, 30, 88, 74
    width = margin * 2 + row_label_w + len(sets) * cell_w + (len(sets) - 1) * gap
    height = header_h + margin + page_count * (cell_h + gap) + margin
    board = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(board)
    draw.text((margin, 18), f"Editable PPT comparison · round {round_number:02d}", fill=INK, font=font(30, bold=True))
    draw.text((margin, 55), "Before and three independently editable candidates", fill=MUTED, font=font(17))

    x0 = margin + row_label_w
    for column, (label, _) in enumerate(sets):
        x = x0 + column * (cell_w + gap)
        draw.rounded_rectangle((x, header_h - 3, x + cell_w, header_h + 28), radius=7, fill=ACCENT if label != "BEFORE" else INK)
        box = draw.textbbox((0, 0), label, font=font(17, bold=True))
        draw.text((x + (cell_w - (box[2] - box[0])) / 2, header_h + 2), label, fill="white", font=font(17, bold=True))

    for page_index in range(page_count):
        y = header_h + margin + page_index * (cell_h + gap)
        draw.text((margin, y + 8), f"P{page_index + 1}", fill=INK, font=font(20, bold=True))
        for column, (_, items) in enumerate(sets):
            x = x0 + column * (cell_w + gap)
            source = safe_image(items, page_index, (cell_w, cell_h))
            board.paste(fit_panel(source, (cell_w, cell_h)), (x, y))
            draw.rectangle((x, y, x + cell_w, y + cell_h), outline="#cbd5e1", width=2)
    output.parent.mkdir(parents=True, exist_ok=True)
    board.save(output, quality=94)


def pair_board(before: Image.Image, after: Image.Image, label: str, page: int) -> Image.Image:
    cell_w, cell_h = 720, 405
    margin, gap, header = 32, 24, 78
    board = Image.new("RGB", (margin * 2 + cell_w * 2 + gap, header + cell_h + margin), BG)
    draw = ImageDraw.Draw(board)
    draw.text((margin, 16), f"Slide {page} · before vs {label}", fill=INK, font=font(28, bold=True))
    for index, (name, item) in enumerate((("BEFORE", before), (label, after))):
        x = margin + index * (cell_w + gap)
        draw.text((x, 52), name, fill=MUTED if index == 0 else ACCENT, font=font(16, bold=True))
        board.paste(fit_panel(item, (cell_w, cell_h)), (x, header))
        draw.rectangle((x, header, x + cell_w, header + cell_h), outline="#cbd5e1", width=2)
    return board


def vertical_montage(images: Iterable[Image.Image]) -> Image.Image:
    boards = list(images)
    if not boards:
        raise ValueError("No comparison pages")
    gap = 20
    width = max(image.width for image in boards)
    height = sum(image.height for image in boards) + gap * (len(boards) - 1)
    result = Image.new("RGB", (width, height), BG)
    y = 0
    for image in boards:
        result.paste(image, (0, y))
        y += image.height + gap
    return result


def make_pair_outputs(before: list[Path], candidate: list[Path], label: str, output: Path) -> list[Path]:
    page_count = max(len(before), len(candidate))
    page_outputs: list[Path] = []
    boards: list[Image.Image] = []
    fallback = (1600, 900)
    for index in range(page_count):
        board = pair_board(
            safe_image(before, index, fallback),
            safe_image(candidate, index, fallback),
            label,
            index + 1,
        )
        target = output / f"slide_{index + 1:03d}_before_vs_{label.lower()}.png"
        board.save(target, quality=94)
        page_outputs.append(target)
        boards.append(board)
    montage = output / f"before_vs_{label.lower()}_montage.png"
    vertical_montage(boards).save(montage, quality=94)
    return [montage, *page_outputs]


def compare_rounds(previous: Path, current: Path, target: Path) -> None:
    board = pair_board(load_rgb(previous), load_rgb(current), "CURRENT ROUND", 0)
    draw = ImageDraw.Draw(board)
    draw.rectangle((0, 0, board.width, 78), fill=BG)
    draw.text((32, 16), "Previous round vs current round overview", fill=INK, font=font(28, bold=True))
    board.save(target, quality=94)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--a", required=True)
    parser.add_argument("--b", required=True)
    parser.add_argument("--c", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--previous-overview")
    args = parser.parse_args()

    sets = [
        ("BEFORE", images_at(Path(args.before))),
        ("A", images_at(Path(args.a))),
        ("B", images_at(Path(args.b))),
        ("C", images_at(Path(args.c))),
    ]
    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    overview = output / f"round_{args.round:02d}_overview.png"
    make_overview(sets, overview, args.round)

    created = [overview]
    before = sets[0][1]
    for label, candidates in sets[1:]:
        created.extend(make_pair_outputs(before, candidates, label, output))

    if args.previous_overview:
        previous = Path(args.previous_overview).expanduser().resolve()
        target = output / "previous_round_vs_current_round_overview.png"
        compare_rounds(previous, overview, target)
        created.append(target)

    print("\n".join(str(path) for path in created))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
