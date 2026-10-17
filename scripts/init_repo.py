#!/usr/bin/env python3
"""Turn a fresh copy of fde-01-foundations into a phase repo.

Renames the Python package and replaces template names everywhere.

Usage (run once, right after `gh repo create ... --template sundayayandele/fde-01-foundations`):
    python scripts/init_repo.py --repo fde-00-programming --package complaints_ingest
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".tf", ".json", ".mmd", ".sh",
                 ".example", ".tpl", ".txt", ".cfg"}
TEXT_NAMES = {"Makefile", "Dockerfile", ".gitignore", ".dockerignore", ".starterignore",
              ".env.example"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="e.g. fde-00-programming")
    parser.add_argument("--package", required=True,
                        help="Python package name, e.g. complaints_ingest")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)

    if not re.fullmatch(r"fde-\d{2}-[a-z0-9-]+", args.repo):
        print("repo must look like fde-NN-name", file=sys.stderr)
        return 1
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.package):
        print("package must be a valid lowercase Python identifier", file=sys.stderr)
        return 1

    root = args.root.resolve()
    service = args.repo.removeprefix("fde-").split("-", 1)[1]  # e.g. programming
    replacements = [
        ("complaint_router", args.package),
        ("fde-01-foundations", args.repo),
        ("fde-01-foundations", f"{args.repo}"),
    ]

    old_pkg = root / "src" / "complaint_router"
    if old_pkg.exists():
        old_pkg.rename(root / "src" / args.package)
    old_chart = root / "deploy" / "helm" / "fde-01-foundations"
    if old_chart.exists():
        old_chart.rename(root / "deploy" / "helm" / args.repo)

    changed = 0
    for path in root.rglob("*"):
        if set(path.relative_to(root).parts) & SKIP or not path.is_file():
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            continue
        text = path.read_text(encoding="utf-8")
        new = text
        for old, value in replacements:
            new = new.replace(old, value)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"init_repo: {args.repo} (package {args.package}, service '{service}'); "
          f"{changed} files updated. Next: edit README.md and docs/, then `make test`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
