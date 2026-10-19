from __future__ import annotations

import argparse
from pathlib import Path

from pattern_core import export_all, image_to_grid


def main() -> int:
    parser = argparse.ArgumentParser(description="图片转 MARD 拼豆网格")
    parser.add_argument("image", type=Path)
    parser.add_argument("--size", type=int, default=30)
    parser.add_argument("--name", default="pindou-pattern")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--keep-background", action="store_true")
    args = parser.parse_args()

    if not args.image.is_file():
        parser.error(f"图片不存在: {args.image}")
    if not 10 <= args.size <= 80:
        parser.error("--size 需要在 10 到 80 之间")
    grid = image_to_grid(args.image, args.size, keep_background=args.keep_background)
    summary = export_all(grid, args.name, args.output_dir)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
