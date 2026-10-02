"""Tests for whereami. Standard library plus pytest, no fixtures beyond tmp_path."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

import whereami


def make_repo(path: Path, when: datetime | None = None) -> None:
    """Create a git repo at path with one commit, optionally dated."""
    path.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    if when is not None:
        stamp = when.isoformat() + " +0000"
        env["GIT_AUTHOR_DATE"] = stamp
        env["GIT_COMMITTER_DATE"] = stamp
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=path,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.email=t@e.com",
            "-c",
            "user.name=T",
            "commit",
            "--allow-empty",
            "-m",
            "x",
        ],
        cwd=path,
        check=True,
        capture_output=True,
        env=env,
    )


def _store(root: Path, projects: dict) -> dict:
    return {"roots": [root.as_posix()], "projects": projects}


def test_bang_fires_when_commit_is_newer_than_stage(tmp_path: Path) -> None:
    """Catches the ! flag silently stopping: it is the entire value of the tool."""
    now = whereami.utc_now()
    root = tmp_path / "root"
    root.mkdir()
    make_repo(root / "Suspect", when=now - timedelta(hours=1))
    make_repo(root / "Quiet", when=now - timedelta(days=10))

    store = _store(
        root,
        {
            "Suspect": {
                "stage": "building",
                "note": "",
                "stage_set_at": (now - timedelta(days=2)).isoformat(),
            },
            "Quiet": {
                "stage": "building",
                "note": "",
                "stage_set_at": (now - timedelta(days=1)).isoformat(),
            },
        },
    )
    rows = {row.name: row for row in whereami.build_rows(store, now)}

    assert "!" in rows["Suspect"].flags
    assert "!" not in rows["Quiet"].flags


def test_folder_with_no_git_degrades(tmp_path: Path) -> None:
    """Catches a git call raising on a plain folder instead of degrading to no git."""
    now = whereami.utc_now()
    root = tmp_path / "root"
    (root / "Plain").mkdir(parents=True)

    rows = whereami.build_rows(_store(root, {}), now)
    plain = {row.name: row for row in rows}["Plain"]

    assert "no git" in plain.flags
    assert "!" not in plain.flags
    assert plain.has_git is False
    assert plain.last_commit is None


def test_suspect_row_sorts_above_older_quiet_row(tmp_path: Path) -> None:
    """Catches the sort losing the hoist: a suspect row must outrank an older quiet one."""
    now = whereami.utc_now()
    root = tmp_path / "root"
    root.mkdir()
    make_repo(root / "Suspect", when=now - timedelta(hours=1))
    make_repo(root / "Quiet", when=now - timedelta(days=40))

    store = _store(
        root,
        {
            "Suspect": {
                "stage": "building",
                "note": "",
                "stage_set_at": (now - timedelta(days=2)).isoformat(),
            },
            # Quiet's stage was set AFTER its last commit, so it carries no "!".
            # If this were older than the commit it would be suspect too, and the
            # staler-first rule inside the suspect group would correctly put it first.
            "Quiet": {
                "stage": "building",
                "note": "",
                "stage_set_at": (now - timedelta(days=30)).isoformat(),
            },
        },
    )
    # ParkedNoGit matches both the parked and the no-git group. No git has to
    # win: while it was grouped as parked, its absent commit date read as oldest
    # and hoisted it above the real parked repo.
    (root / "ParkedNoGit").mkdir()
    make_repo(root / "ParkedRepo", when=now - timedelta(days=5))
    store["projects"]["ParkedNoGit"] = {
        "stage": "parked",
        "note": "",
        "stage_set_at": (now - timedelta(days=90)).isoformat(),
    }
    # Stage set AFTER its last commit, so ParkedRepo carries no "!" and the
    # grouping rule is what this assertion actually exercises.
    store["projects"]["ParkedRepo"] = {
        "stage": "parked",
        "note": "",
        "stage_set_at": (now - timedelta(days=1)).isoformat(),
    }
    names = [row.name for row in whereami.build_rows(store, now)]

    assert names.index("Suspect") < names.index("Quiet")
    assert names.index("ParkedRepo") < names.index("ParkedNoGit")


def test_invalid_stage_exits_two_without_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a rejected stage still rewriting the store."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(whereami, "store_path", lambda: store_file)
    store_file.write_text('{"roots": [], "projects": {"X": {"stage": "idea"}}}')
    before = store_file.read_bytes()

    code = whereami.main(["set", "X", "nonsense"])

    assert code == 2
    assert store_file.read_bytes() == before


def test_set_stamps_stage_set_at(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a write path forgetting stage_set_at, which silently kills every flag."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(whereami, "store_path", lambda: store_file)
    store_file.write_text('{"roots": [], "projects": {"X": {"stage": "idea"}}}')

    code = whereami.main(["set", "X", "building"])

    assert code == 0
    stored = whereami.load_store(store_file)["projects"]["X"]
    stamped = datetime.fromisoformat(stored["stage_set_at"])
    assert abs((whereami.utc_now() - stamped).total_seconds()) < 60


def test_init_persists_the_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a mutating command printing success without writing the store."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(whereami, "store_path", lambda: store_file)
    root = tmp_path / "root"
    (root / "Alpha").mkdir(parents=True)
    (root / ".hidden").mkdir()

    assert whereami.main(["init", str(root)]) == 0

    saved = json.loads(store_file.read_text(encoding="utf-8"))
    assert root.resolve().as_posix() in saved["roots"]
    assert "Alpha" in saved["projects"]
    assert ".hidden" not in saved["projects"]
