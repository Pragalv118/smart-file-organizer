# Smart File Organizer

A small Python CLI that sorts a messy folder (like Downloads) into category subfolders — `Images`, `Documents`, `Videos`, `Audio`, `Archives`, `Code`, `Other` — based on file extension.

## Why

Manually sorting a cluttered folder gets old fast. This script automates it safely: it previews changes with `--dry-run`, logs every move, and can undo the most recent run if something goes wrong.

## Features

- Sorts files into category folders by extension
- `--dry-run` to preview without touching anything
- `--recursive` to include subfolders
- Collision-safe — never overwrites an existing file, appends a numeric suffix instead
- `--undo` reverts the most recent run using a JSON log
- No third-party dependencies — pure Python standard library
- Unit tested with pytest, CI runs on every push

## Usage

```bash
# Preview what would happen in the current directory
python3 organizer.py --dry-run

# Organize ~/Downloads, including subfolders
python3 organizer.py ~/Downloads --recursive

# Undo the last run
python3 organizer.py ~/Downloads --undo
```

## Running tests

```bash
pip install pytest
pytest -v
```

## Project structure

```
organizer.py                  CLI + sorting logic
tests/test_organizer.py       unit tests
.github/workflows/tests.yml   CI
```

## License

MIT
