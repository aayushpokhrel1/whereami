"""Build a throwaway set of repos in a temp directory and print the board for them.

This exists so the README image is real tool output without exposing anyone's
actual project list. Regenerate the image with:

    python scripts/demo_board.py | python scripts/board_svg.py > docs/board.svg

Do NOT pipe a real `whereami` board into board_svg.py for the README: it would
publish every project name and note on the machine that ran it.
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import whereami  # noqa: E402

NOW = whereami.utc_now()

# name, days since last commit, stage, days since stage set (None = no git folder),
# note, dirty, unpushed
# Stage set BEFORE the last commit makes a row suspect. Two rows are, which is
# the point of the image; the rest are calm so the flags still read as signal.
DEMO = [
    ("api-gateway", 2, "shipped", 20, "live, three regions", False, 0),
    ("checkout-rewrite", 1, "building", 44, "payment split half migrated", True, 0),
    ("mobile-client", 31, "spec", 20, "waiting on the auth decision", False, 0),
    ("ingest-worker", 17, "building", 10, "backfill still manual", False, 5),
    ("docs-site", 9, "shipped", 5, "", False, 0),
    ("design-system", 5, "testing", 3, "a11y audit in progress", False, 2),
    ("pricing-model", 74, "parked", 70, "revisit after Q1", False, 0),
    ("scratch-notebooks", None, "idea", None, "", False, 0),
]


def run(args, cwd, env=None):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, env=env)


def make_repo(path: Path, days: int, dirty: bool, unpushed: int) -> None:
    path.mkdir(parents=True)
    run(["git", "init", "-b", "main"], path)
    env = os.environ.copy()
    stamp = (NOW - timedelta(days=days)).isoformat() + " +0000"
    env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = stamp
    run(
        ["git", "-c", "user.email=d@e.com", "-c", "user.name=D", "-c",
         "commit.gpgsign=false", "commit", "--allow-empty", "-m", "work"],
        path, env,
    )
    if unpushed:
        # A bare clone as upstream, cloned BEFORE the extra commits, so they read
        # as unpushed.
        bare = path.parent.parent / "upstreams" / (path.name + ".git")
        bare.parent.mkdir(exist_ok=True)
        run(["git", "clone", "--bare", str(path), str(bare)], path.parent)
        run(["git", "remote", "add", "origin", str(bare)], path)
        # The remote-tracking ref does not exist until a fetch, and
        # --set-upstream-to refuses without it.
        run(["git", "fetch", "-q", "origin"], path)
        run(["git", "branch", "--set-upstream-to=origin/main", "main"], path)
        for i in range(unpushed):
            run(
                ["git", "-c", "user.email=d@e.com", "-c", "user.name=D", "-c",
                 "commit.gpgsign=false", "commit", "--allow-empty", "-m", f"more {i}"],
                path, env,
            )
    if dirty:
        (path / "wip.txt").write_text("unsaved\n", encoding="utf-8")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="whereami-demo-"))
    root = tmp / "code"
    root.mkdir()
    projects = {}
    for name, days, stage, stage_days, note, dirty, unpushed in DEMO:
        if days is None:
            (root / name).mkdir()
        else:
            make_repo(root / name, days, dirty, unpushed)
        projects[name] = {
            "stage": stage,
            "note": note,
            "stage_set_at": None if stage_days is None
            else (NOW - timedelta(days=stage_days)).isoformat(),
        }
    store = tmp / "projects.json"
    store.write_text(
        json.dumps({"roots": [root.as_posix()], "projects": projects}, indent=2),
        encoding="utf-8",
    )
    whereami.store_path = lambda: store
    return whereami.main(["show"])


if __name__ == "__main__":
    sys.exit(main())
