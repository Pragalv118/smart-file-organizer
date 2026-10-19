import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organizer import apply_plan, build_plan, category_for, undo_last_run, write_log


def make_file(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_category_for():
    assert category_for(Path("a.jpg")) == "Images"
    assert category_for(Path("a.py")) == "Code"
    assert category_for(Path("a.unknownext")) == "Other"


def test_build_and_apply_plan(tmp_path):
    make_file(tmp_path / "photo.png")
    make_file(tmp_path / "notes.txt")

    plan = build_plan(tmp_path, recursive=False)
    assert len(plan) == 2

    executed = apply_plan(plan, dry_run=False)
    assert (tmp_path / "Images" / "photo.png").exists()
    assert (tmp_path / "Documents" / "notes.txt").exists()
    assert len(executed) == 2


def test_dry_run_does_not_move(tmp_path):
    make_file(tmp_path / "song.mp3")
    plan = build_plan(tmp_path, recursive=False)
    executed = apply_plan(plan, dry_run=True)
    assert executed == []
    assert (tmp_path / "song.mp3").exists()
    assert not (tmp_path / "Audio").exists()


def test_name_collision_gets_suffixed(tmp_path):
    make_file(tmp_path / "Images" / "dup.jpg", "existing")
    make_file(tmp_path / "dup.jpg", "new")

    plan = build_plan(tmp_path, recursive=True)
    assert len(plan) == 1
    src, dest = plan[0]
    assert src.name == "dup.jpg"
    assert dest.name == "dup_1.jpg"


def test_undo_restores_files(tmp_path):
    make_file(tmp_path / "report.pdf")
    plan = build_plan(tmp_path, recursive=False)
    executed = apply_plan(plan, dry_run=False)
    write_log(tmp_path, executed)
    assert (tmp_path / "Documents" / "report.pdf").exists()

    restored = undo_last_run(tmp_path, dry_run=False)
    assert restored == 1
    assert (tmp_path / "report.pdf").exists()
    assert not (tmp_path / "Documents" / "report.pdf").exists()
