# Operations

## Run

```bash
python whereami.py            # straight from source, no install
uv tool install .             # install the console script locally
whereami                      # then this works anywhere
```

## Verify

```bash
python -m pytest              # the suite
python test_whereami.py       # the same assertions as a standalone self-check
```

The suite builds throwaway git repos in a temp directory and commits to them, so it needs
`git` on PATH and a committer identity. CI sets one; locally your global `user.name` and
`user.email` cover it. If a test fails with "Author identity unknown", that is the cause.

## Release

PyPI, when the tool is ready to publish:

```bash
uv build
uv publish                    # needs a PyPI token in UV_PUBLISH_TOKEN
```

Bump `version` in `pyproject.toml` first. Tag the commit to match.

## Make the board unavoidable

The tool only fixes forgetting if you see the board without deciding to. Two ways:

**Shell profile.** PowerShell (`$PROFILE`):

```powershell
function projects { whereami }
```

Bash or zsh:

```bash
alias projects=whereami
```

**Claude Code SessionStart hook.** Prints the board every time a session opens, in any
project. In `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup", "hooks": [{ "type": "command", "command": "whereami" }] }
    ]
  }
}
```

This hook belongs in your own settings, not in this repo. A tool that edits a stranger's
Claude config on install would be a bad citizen.

## Environment traps

- **Not every folder is a repo.** Three of the eighteen folders this was built against have
  no `.git`. Every git call has to degrade to "no git" rather than raising, and the test
  suite covers that case specifically.
- **`git` must be on PATH.** There is no bundled fallback. If it is missing, every project
  reads as "no git" and the board is useless but does not crash.
- **Windows paths in the store are JSON strings**, so backslashes are escaped. Read them back
  through `pathlib` rather than string-splitting.
- **The store is rewritten whole on every write.** It is a few kilobytes, so this is fine, but
  it means two concurrent `set` commands can lose one of the two. Not worth locking for a
  single-user tool; worth knowing if that ever stops being true.
- **`stage_set_at` is the hinge of the `!` flag.** If a write path ever forgets to update it,
  the flag silently stops firing and the tool quietly becomes a worse `ls`. The test for this
  is the most important one in the suite.
