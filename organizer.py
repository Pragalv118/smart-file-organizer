#!/usr/bin/env python3
"""Sort files in a directory into category subfolders by extension."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path

LOG_FILENAME = ".organizer_log.json"

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"},
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a"},
    "Archives": {".zip", ".tar", ".gz", ".rar", ".7z"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".sh", ".json", ".yml", ".yaml"},
}

logger = logging.getLogger("organizer")


def category_for(path: Path) -> str:
    ext = path.suffix.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def is_organizer_artifact(path: Path, root: Path) -> bool:
    if path.name == LOG_FILENAME:
        return True
    if path.parent != root and path.parent.parent == root and path.parent.name in {*CATEGORIES, "Other"}:
        return True
    return False


def build_plan(root: Path, recursive: bool) -> list[tuple[Path, Path]]:
    pattern = "**/*" if recursive else "*"
    plan: list[tuple[Path, Path]] = []
    for path in sorted(root.glob(pattern)):
        if path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if is_organizer_artifact(path, root):
            continue
        category = category_for(path)
        dest_dir = root / category
        dest = dest_dir / path.name
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{path.stem}_{counter}{path.suffix}"
            counter += 1
        plan.append((path, dest))
    return plan


def apply_plan(plan: list[tuple[Path, Path]], dry_run: bool) -> list[tuple[str, str]]:
    executed: list[tuple[str, str]] = []
    for src, dest in plan:
        logger.info("%s %s -> %s", "[dry-run]" if dry_run else "moving", src, dest)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            executed.append((str(src), str(dest)))
    return executed


def write_log(root: Path, executed: list[tuple[str, str]]) -> None:
    if not executed:
        return
    log_path = root / LOG_FILENAME
    history = json.loads(log_path.read_text()) if log_path.exists() else []
    history.append(executed)
    log_path.write_text(json.dumps(history, indent=2))


def undo_last_run(root: Path, dry_run: bool) -> int:
    log_path = root / LOG_FILENAME
    if not log_path.exists():
        logger.warning("No organizer log found in %s, nothing to undo.", root)
        return 0
    history = json.loads(log_path.read_text())
    if not history:
        logger.warning("Log is empty, nothing to undo.")
        return 0
    last_run = history.pop()
    for src, dest in reversed(last_run):
        src_path, dest_path = Path(src), Path(dest)
        logger.info("%s %s -> %s", "[dry-run]" if dry_run else "restoring", dest_path, src_path)
        if not dry_run and dest_path.exists():
            src_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest_path), str(src_path))
    if not dry_run:
        log_path.write_text(json.dumps(history, indent=2))
    return len(last_run)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sort files in a directory into category subfolders by extension.")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to organize (default: current directory)")
    parser.add_argument("--recursive", action="store_true", help="Include files in subdirectories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without moving anything")
    parser.add_argument("--undo", action="store_true", help="Undo the most recent run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        logger.error("Not a directory: %s", root)
        return 1

    if args.undo:
        count = undo_last_run(root, args.dry_run)
        logger.info("Restored %d file(s).", count)
        return 0

    plan = build_plan(root, args.recursive)
    if not plan:
        logger.info("Nothing to organize in %s", root)
        return 0

    executed = apply_plan(plan, args.dry_run)
    if args.dry_run:
        logger.info("Dry run complete: %d file(s) would be organized.", len(plan))
    else:
        write_log(root, executed)
        categories_touched = len({dest.parent for _, dest in plan})
        logger.info("Organized %d file(s) into %d categor%s.", len(executed), categories_touched, "y" if categories_touched == 1 else "ies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
