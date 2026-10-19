from __future__ import annotations

import argparse
from pathlib import Path

from pattern_core import export_all, read_grid


def main() -> int:
    parser = argparse.ArgumentParser(description="渲染已有 MARD 拼豆网格")
    parser.add_argument("grid", type=Path)
    parser.add_argument("--name", default="pindou-pattern")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()

    if not args.grid.is_file():
        parser.error(f"网格不存在: {args.grid}")
    summary = export_all(read_grid(args.grid), args.name, args.output_dir)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
