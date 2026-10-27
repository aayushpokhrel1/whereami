"""Tests for wipboard. Standard library plus pytest, no fixtures beyond tmp_path."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta
import codecs
import json
from pathlib import Path

import pytest

import wipboard


def make_repo(path: Path, when: datetime | None = None, message: str = "work") -> None:
    """Create a git repo at path with one commit, optionally dated and messaged."""
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
            # Git refuses an empty message without this, and an empty subject is
            # exactly the case the %cI%n%s split has to survive.
            "--allow-empty-message",
            "-m",
            message,
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
    now = wipboard.utc_now()
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
    rows = {row.name: row for row in wipboard.build_rows(store, now)}

    assert "!" in rows["Suspect"].flags
    assert "!" not in rows["Quiet"].flags


def test_folder_with_no_git_degrades(tmp_path: Path) -> None:
    """Catches a git call raising on a plain folder instead of degrading to no git."""
    now = wipboard.utc_now()
    root = tmp_path / "root"
    (root / "Plain").mkdir(parents=True)

    rows = wipboard.build_rows(_store(root, {}), now)
    plain = {row.name: row for row in rows}["Plain"]

    assert "no git" in plain.flags
    assert "!" not in plain.flags
    assert plain.has_git is False
    assert plain.last_commit is None


def test_suspect_row_sorts_above_older_quiet_row(tmp_path: Path) -> None:
    """Catches the sort losing the hoist: a suspect row must outrank an older quiet one."""
    now = wipboard.utc_now()
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
    names = [row.name for row in wipboard.build_rows(store, now)]

    assert names.index("Suspect") < names.index("Quiet")
    assert names.index("ParkedRepo") < names.index("ParkedNoGit")


def test_invalid_stage_exits_two_without_writing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a rejected stage still rewriting the store."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(wipboard, "store_path", lambda: store_file)
    store_file.write_text('{"roots": [], "projects": {"X": {"stage": "idea"}}}')
    before = store_file.read_bytes()

    code = wipboard.main(["set", "X", "nonsense"])

    assert code == 2
    assert store_file.read_bytes() == before


def test_set_stamps_stage_set_at(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a write path forgetting stage_set_at, which silently kills every flag."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(wipboard, "store_path", lambda: store_file)
    store_file.write_text('{"roots": [], "projects": {"X": {"stage": "idea"}}}')

    code = wipboard.main(["set", "X", "building"])

    assert code == 0
    stored = wipboard.load_store(store_file)["projects"]["X"]
    stamped = datetime.fromisoformat(stored["stage_set_at"])
    assert abs((wipboard.utc_now() - stamped).total_seconds()) < 60


def test_init_persists_the_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a mutating command printing success without writing the store."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(wipboard, "store_path", lambda: store_file)
    root = tmp_path / "root"
    (root / "Alpha").mkdir(parents=True)
    (root / ".hidden").mkdir()

    assert wipboard.main(["init", str(root)]) == 0

    saved = json.loads(store_file.read_text(encoding="utf-8"))
    assert root.resolve().as_posix() in saved["roots"]
    assert "Alpha" in saved["projects"]
    assert ".hidden" not in saved["projects"]


def test_git_info_returns_subject_and_changed_count(tmp_path: Path) -> None:
    """Catches a second git process per repo, and a crash on an empty subject."""
    repo = tmp_path / "r"
    make_repo(repo, message="Add the thing")
    info = wipboard.git_info(repo)
    assert info["subject"] == "Add the thing"
    assert info["changed"] == 0


def test_empty_commit_subject_does_not_raise(tmp_path: Path) -> None:
    """Review Focus 2: --format=%cI%n%s yields one part when the subject is empty."""
    repo = tmp_path / "r"
    make_repo(repo, message="")
    info = wipboard.git_info(repo)
    assert info["subject"] == ""


def test_rows_carry_stage_set_at_and_branch(tmp_path: Path) -> None:
    """Catches build_rows dropping the fields the dashboard renders."""
    now = wipboard.utc_now()
    root = tmp_path / "root"
    root.mkdir()
    make_repo(root / "Alpha")
    store = _store(
        root,
        {
            "Alpha": {
                "stage": "building",
                "note": "",
                "stage_set_at": (now - timedelta(days=2)).isoformat(),
            },
        },
    )

    row = {row.name: row for row in wipboard.build_rows(store, now)}["Alpha"]

    assert row.branch == "main"
    assert isinstance(row.stage_set_at, datetime)


def test_board_payload_shape():
    # This dict is the contract the Worker parses. A silent key rename breaks the
    # dashboard with no local failure, so the shape is asserted exactly.
    rows = [
        wipboard.Row(name="alpha", stage="building", note="n",
                     last_commit=datetime(2026, 10, 20, 12, 0), flags=["!"],
                     has_git=True, branch="main", subject="s", changed=2,
                     stage_set_at=datetime(2026, 10, 1, 9, 0)),
        wipboard.Row(name="beta", stage="idea", note="", last_commit=None,
                     flags=["no git"], has_git=False),
    ]
    p = wipboard.board_payload(rows, datetime(2026, 10, 20, 12, 5), "HOST")
    assert p["version"] == 1
    assert p["generated_at"] == "2026-10-20T12:05:00"
    assert p["host"] == "HOST"
    assert p["projects"][0] == {
        "name": "alpha", "stage": "building", "note": "n",
        "last_commit": "2026-10-20T12:00:00", "stage_set_at": "2026-10-01T09:00:00",
        "flags": ["!"], "has_git": True, "branch": "main", "subject": "s", "changed": 2,
    }
    assert p["projects"][1]["last_commit"] is None
    assert p["projects"][1]["stage_set_at"] is None


def test_push_without_config_exits_two_and_leaves_store_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Catches push rewriting or clearing the store on a failure path."""
    store_file = tmp_path / "projects.json"
    monkeypatch.setattr(wipboard, "store_path", lambda: store_file)
    # HOME decides where the config file is looked for, so point it at an empty
    # directory rather than trusting the machine running the tests.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("WIPBOARD_ENDPOINT", raising=False)
    monkeypatch.delenv("WIPBOARD_TOKEN", raising=False)
    store_file.write_text('{"roots": [], "projects": {"X": {"stage": "idea"}}}')
    before = store_file.read_bytes()

    # No network: _post is replaced, so a push that got this far would fail loudly
    # rather than reach out.
    def explode(url: str, token: str, body: bytes) -> int:
        raise AssertionError("push made a network call with no configuration")

    monkeypatch.setattr(wipboard, "_post", explode)

    assert wipboard.main(["push"]) == 2
    assert store_file.read_bytes() == before


def test_env_overrides_config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The scheduled task passes env vars and has no config file."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("WIPBOARD_ENDPOINT", "https://e.example/api/board")
    monkeypatch.setenv("WIPBOARD_TOKEN", "t")
    assert wipboard.push_config() == ("https://e.example/api/board", "t")


def test_config_with_a_utf8_bom_is_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a BOM making a valid config look absent.

    PowerShell's Set-Content -Encoding utf8 writes one, so this is the normal
    way the file gets created on Windows, not an exotic case.
    """
    cfg = tmp_path / "config.json"
    cfg.write_bytes(
        codecs.BOM_UTF8 + json.dumps({"endpoint": "https://e/api", "token": "t"}).encode()
    )
    monkeypatch.setattr(wipboard, "config_path", lambda: cfg)
    monkeypatch.delenv("WIPBOARD_ENDPOINT", raising=False)
    monkeypatch.delenv("WIPBOARD_TOKEN", raising=False)
    assert wipboard.push_config() == ("https://e/api", "t")


def test_unreadable_config_reports_itself(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches a broken config being reported as a missing key."""
    cfg = tmp_path / "config.json"
    cfg.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(wipboard, "config_path", lambda: cfg)
    monkeypatch.delenv("WIPBOARD_ENDPOINT", raising=False)
    monkeypatch.delenv("WIPBOARD_TOKEN", raising=False)
    with pytest.raises(wipboard.ConfigError, match="Cannot read"):
        wipboard.push_config()


def test_post_sends_a_descriptive_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Catches the push falling back to urllib's default agent.

    Cloudflare's browser integrity check bans Python-urllib by signature and
    returns 403 error 1010 from the edge, so the bearer token never gets looked
    at and the failure looks like an auth problem instead of a user-agent one.
    """
    seen: dict[str, str] = {}

    class _Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout=None):
        seen.update(request.headers)
        return _Response()

    monkeypatch.setattr(wipboard.urllib.request, "urlopen", fake_urlopen)
    assert wipboard._post("https://e/api", "t", b"{}") == 204
    agent = seen.get("User-agent", "")
    assert agent.startswith("wipboard/")
    assert "Python-urllib" not in agent


def test_documented_test_counts_match_reality() -> None:
    """Catches the docs stating a test count that stopped being true.

    Every sweep of this repo has found a stale count in docs/OPERATIONS.md: it
    said 12 Python tests when there were 15, and 17 Worker tests when there were
    25. A number in prose rots silently because nothing recounts it. This recounts
    it. If it fails, fix the document rather than the number here.
    """
    import re

    root = Path(__file__).resolve().parent
    ops = (root / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")

    actual_py = len(re.findall(r"^def test_", (root / "test_wipboard.py").read_text(encoding="utf-8"), re.M))
    stated_py = int(re.search(r"# (\d+) tests, the whole suite", ops).group(1))
    assert stated_py == actual_py, f"OPERATIONS.md says {stated_py} Python tests, there are {actual_py}"

    worker_tests = sorted((root / "worker" / "test").glob("*.test.ts"))
    assert worker_tests, "no Worker tests found; the glob or the layout changed"
    actual_worker = sum(
        len(re.findall(r"^\s*it\(", f.read_text(encoding="utf-8"), re.M)) for f in worker_tests
    )
    stated_worker = int(re.search(r"^(\d+) tests plus `tsc", ops, re.M).group(1))
    assert stated_worker == actual_worker, (
        f"OPERATIONS.md says {stated_worker} Worker tests, there are {actual_worker}"
    )
