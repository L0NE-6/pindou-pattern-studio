from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PALETTE = {
    "C16": (22, 88, 166),
    "H2": (253, 251, 254),
    "H8": (43, 43, 46),
    "D10": (48, 27, 75),
    "D4": (24, 42, 131),
    "C29": (54, 72, 137),
    "E16": (250, 242, 236),
    "H4": (134, 133, 137),
    "D2": (135, 139, 218),
    "H11": (202, 201, 204),
    "C24": (122, 195, 250),
    "C6": (83, 169, 234),
    "D16": (227, 225, 237),
    "E15": (245, 198, 200),
    "H7": (0, 2, 1),
    "D24": (117, 132, 227),
    "G9": (227, 178, 132),
    "C12": (27, 51, 75),
    "C13": (203, 231, 251),
    "C8": (18, 81, 193),
    "D3": (44, 83, 171),
}
EMPTY = {"", "·", ".", "-"}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def lum(color: tuple[int, int, int]) -> float:
    return 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]


def normalize_grid(rows: Iterable[Iterable[str]]) -> list[list[str]]:
    grid = [[("" if str(code).strip() in EMPTY else str(code).strip().upper()) for code in row] for row in rows]
    if not grid or not grid[0]:
        raise ValueError("网格为空")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("网格各行列数不一致")
    unknown = sorted({code for row in grid for code in row if code and code not in PALETTE})
    if unknown:
        raise ValueError(f"未知色号: {', '.join(unknown)}")
    return grid


def read_grid(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        raise ValueError("CSV 为空")
    if rows[0] and not rows[0][0].strip():
        rows = rows[1:]
    grid = []
    for row in rows:
        if not row:
            continue
        values = row[1:] if row[0].strip().lower().startswith("row") else row
        grid.append(values)
    return normalize_grid(grid)


def save_grid(grid: list[list[str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([""] + [f"col{i + 1}" for i in range(len(grid[0]))])
        for index, row in enumerate(grid, 1):
            writer.writerow([f"row{index}"] + [code or "·" for code in row])


def nearest_palette(color: tuple[int, int, int]) -> str:
    return min(
        PALETTE,
        key=lambda code: (
            (color[0] - PALETTE[code][0]) ** 2
            + (color[1] - PALETTE[code][1]) ** 2
            + (color[2] - PALETTE[code][2]) ** 2
        ),
    )


def image_to_grid(image_path: Path, size: int, *, keep_background: bool = False) -> list[list[str]]:
    source = Image.open(image_path).convert("RGBA")
    if not keep_background:
        pixels = source.load()
        opaque_points = [
            (x, y)
            for y in range(source.height)
            for x in range(source.width)
            if pixels[x, y][3] > 24
            and (
                pixels[x, y][3] < 240
                or min(pixels[x, y][:3]) < 242
                or max(pixels[x, y][:3]) - min(pixels[x, y][:3]) > 12
            )
        ]
        if opaque_points:
            xs = [point[0] for point in opaque_points]
            ys = [point[1] for point in opaque_points]
            source = source.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))

    side = max(source.size)
    square = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    square.alpha_composite(
        source,
        ((side - source.width) // 2, (side - source.height) // 2),
    )
    sample = square.resize((size, size), Image.Resampling.LANCZOS)
    pixels = sample.load()
    grid: list[list[str]] = []
    for y in range(size):
        row = []
        for x in range(size):
            r, g, b, a = pixels[x, y]
            is_empty = a < 40 or (
                not keep_background
                and min(r, g, b) >= 242
                and max(r, g, b) - min(r, g, b) <= 12
            )
            row.append("" if is_empty else nearest_palette((r, g, b)))
        grid.append(row)
    return outline_grid(grid)


def outline_grid(grid: list[list[str]]) -> list[list[str]]:
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for y in range(height):
        for x in range(width):
            if not grid[y][x]:
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if ny < 0 or ny >= height or nx < 0 or nx >= width or not grid[ny][nx]:
                    result[y][x] = "H8"
                    break
    return result


def validate_outline(grid: list[list[str]]) -> list[dict[str, int]]:
    height, width = len(grid), len(grid[0])
    errors = []
    for y in range(height):
        for x in range(width):
            if not grid[y][x]:
                continue
            boundary = any(
                ny < 0
                or ny >= height
                or nx < 0
                or nx >= width
                or not grid[ny][nx]
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
                for ny, nx in [(y + dy, x + dx)]
            )
            if boundary and grid[y][x] != "H8":
                errors.append({"row": y + 1, "column": x + 1})
    return errors


def render_chart(grid: list[list[str]], name: str, path: Path) -> dict[str, int]:
    width, height = len(grid[0]), len(grid)
    counts = Counter(code for row in grid for code in row if code)
    cell = 32
    pad = 46
    legend_rows = (len(counts) + 5) // 6
    image = Image.new("RGB", (pad * 2 + cell * width, 120 + cell * height + legend_rows * 74), "white")
    draw = ImageDraw.Draw(image)
    draw.text(
        (14, 8),
        f"{name} [{width}x{height}/MARD/{len(counts)}色/共{sum(counts.values())}颗]",
        font=font(22, True),
        fill="#111111",
    )
    draw.text((14, 40), "Perler Beads Chart · 空格=不放豆", font=font(13), fill="#666666")
    x0, y0 = pad, 64
    for index in range(max(width, height) + 1):
        if index <= width:
            draw.line([(x0 + index * cell, y0), (x0 + index * cell, y0 + cell * height)], fill="#BBBBBB")
        if index <= height:
            draw.line([(x0, y0 + index * cell), (x0 + cell * width, y0 + index * cell)], fill="#BBBBBB")
    for index in range(width):
        draw.text((x0 + index * cell + cell // 2, y0 - 13), str(index + 1), font=font(12), fill="#333333", anchor="mm")
    for index in range(height):
        draw.text((x0 - 13, y0 + index * cell + cell // 2), str(index + 1), font=font(12), fill="#333333", anchor="mm")
    for y, row in enumerate(grid):
        for x, code in enumerate(row):
            if not code:
                continue
            color = PALETTE[code]
            left, top = x0 + x * cell, y0 + y * cell
            draw.rectangle([left + 1, top + 1, left + cell - 1, top + cell - 1], fill=color)
            draw.text(
                (left + cell // 2, top + cell // 2),
                code,
                font=font(11, True),
                fill="white" if lum(color) < 132 else "#1A1A1A",
                anchor="mm",
            )
    legend_y = y0 + height * cell + 44
    draw.line([(14, legend_y), (image.width - 14, legend_y)], fill="#DDDDDD")
    step = (image.width - 32) / 6
    for index, (code, count) in enumerate(sorted(counts.items(), key=lambda item: (-item[1], item[0]))):
        row, column = divmod(index, 6)
        x, y = 16 + column * step, legend_y + 16 + row * 74
        color = PALETTE[code]
        draw.rounded_rectangle([x, y, x + 96, y + 34], 8, fill=color, outline="#888888")
        draw.text(
            (x + 48, y + 17),
            code,
            font=font(16, True),
            fill="white" if lum(color) < 132 else "#1A1A1A",
            anchor="mm",
        )
        draw.text((x + 104, y + 17), f"×{count}", font=font(15), fill="#222222", anchor="lm")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return dict(counts)


def render_preview(grid: list[list[str]], path: Path, bead: int = 40) -> None:
    width, height = len(grid[0]), len(grid)
    image = Image.new("RGB", (bead * width + 20, bead * height + 20), "white")
    draw = ImageDraw.Draw(image)
    radius = int(bead * 0.43)
    hole = max(2, int(bead * 0.11))
    for y, row in enumerate(grid):
        for x, code in enumerate(row):
            if not code:
                continue
            color = PALETTE[code]
            cx, cy = 10 + x * bead + bead // 2, 10 + y * bead + bead // 2
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=color,
                outline=tuple(max(0, value - 45) for value in color),
            )
            draw.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], fill="white")
            draw.arc(
                [cx - radius + 2, cy - radius + 2, cx + radius - 2, cy + radius - 2],
                200,
                330,
                fill=tuple(min(255, value + 60) for value in color),
                width=3,
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def export_all(grid: list[list[str]], name: str, output_dir: Path) -> dict[str, object]:
    counts = render_chart(grid, name, output_dir / f"{name}_chart.png")
    render_preview(grid, output_dir / f"{name}_preview.png")
    save_grid(grid, output_dir / f"{name}_grid.csv")
    summary = {
        "name": name,
        "width": len(grid[0]),
        "height": len(grid),
        "colors": counts,
        "total_beads": sum(counts.values()),
        "outline_errors": validate_outline(grid),
    }
    (output_dir / f"{name}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary
