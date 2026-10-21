# Operations

## Run

```bash
python wipboard.py            # straight from source, no install
uv tool install .             # install the console script locally
wipboard                      # then this works anywhere
```

## Verify

```bash
python -m pytest              # 12 tests, the whole suite
```

**pytest is required.** `python test_wipboard.py` runs nothing and exits 0, because the tests
take pytest fixtures and the file has no `__main__` block. This file claimed otherwise until
2026-10-21, which is worse than saying nothing: it hands you a green exit code from a command
that tested none of the code.

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
function projects { wipboard }
```

Bash or zsh:

```bash
alias projects=wipboard
```

**Claude Code SessionStart hook.** Prints the board every time a session opens, in any
project. In `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "startup", "hooks": [{ "type": "command", "command": "wipboard" }] }
    ]
  }
}
```

This hook belongs in your own settings, not in this repo. A tool that edits a stranger's
Claude config on install would be a bad citizen.

## The dashboard Worker

Optional. `worker/` holds a Cloudflare Worker that stores one pushed board in KV and serves it
as a web page. The CLI does not need it and sends nothing anywhere until `endpoint` is set.

### Verify the Worker

```bash
npm --prefix worker test
```

17 tests, run in the real Workers runtime via `@cloudflare/vitest-pool-workers`, not a mock.

### First deploy

**These steps have not been run end to end yet.** Correct them the first time you do.

```bash
npx wrangler login
```

The KV namespace already exists and its id is in `worker/wrangler.jsonc`. Recreate it only for
a fresh account:

```bash
npx wrangler kv namespace create BOARD
```

Generate a token and set it as a secret. Use a real random value, not a memorable one: it is
the only thing standing between the internet and your board.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
npx wrangler secret put BOARD_TOKEN --config worker/wrangler.jsonc
npx wrangler deploy --config worker/wrangler.jsonc
```

Deploy prints the hostname, `wipboard.<subdomain>.workers.dev`.

### Lock it down BEFORE pushing a real board

A `workers.dev` hostname is public. Your board is a complete list of your projects with candid
notes on each, so **configure access before the first `wipboard push`**, not after. The empty
page is harmless; the populated one is not.

In the Cloudflare Zero Trust dashboard:

1. Access, Applications, Add a self-hosted application for the Worker hostname.
2. Policy: Allow, with an Emails rule naming your address.
3. Add a second policy of type **Bypass** scoped to the path `/api/board`, with an Everyone
   rule.

Step 3 is not optional and is the easiest thing to get wrong. Access authenticates humans
through an email round trip, which a scheduled task cannot complete, so an Access policy
covering the whole hostname locks out your own pusher. `/api/board` is protected instead by
the bearer token, compared in constant time in `worker/src/index.ts`.

Confirm both halves before trusting it: opening the hostname in a private window should
demand a login, and `wipboard push` should still succeed.

### Point the CLI at it

`~/.config/wipboard/config.json`:

```json
{
  "endpoint": "https://wipboard.<subdomain>.workers.dev/api/board",
  "token": "the same value you gave wrangler secret put"
}
```

`WIPBOARD_ENDPOINT` and `WIPBOARD_TOKEN` override the file, which is how a scheduled task
passes them without one. Then:

```bash
wipboard push
```

### Keep it fresh

The page is only as current as the last push, so push on events rather than hoping.

**On every commit, in any repo.** Append to the user-global hook at
`~/.config/git/hooks/post-commit` (the one `core.hooksPath` already points at):

```bash
wipboard push >/dev/null 2>&1 &
```

Backgrounded and silenced on purpose: a commit must never wait on, or fail because of, the
network.

**After a stage change.** `wipboard set ...; wipboard push`.

**Every 15 minutes**, to catch dirty trees and elapsed time, via Task Scheduler:

```powershell
$action = New-ScheduledTaskAction -Execute 'wipboard' -Argument 'push'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName 'wipboard push' -Action $action -Trigger $trigger
```

None of this is installed for you. A tool that edits a stranger's git hooks or schedules tasks
on install would be a bad citizen, which is the same reason the `SessionStart` hook lives in
your Claude settings and not in this repo.

### Rotating BOARD_TOKEN

The naive order leaves a window where every push fails. There is no two-token support in the
Worker, so keep the window short and do it in this order:

1. `npx wrangler secret put BOARD_TOKEN --config worker/wrangler.jsonc` with the new value.
2. Immediately update `token` in `~/.config/wipboard/config.json`.
3. `wipboard push` to confirm.

Pushes between 1 and 2 return 401 and exit 2. Nothing is lost: the next push sends the whole
board, since every push is a full snapshot rather than a delta.

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
- **The local test runtime caps the compatibility date.** `wrangler.jsonc` sets
  `compatibility_date` to the date the Worker was created, but the installed `workerd` only
  supports up to its own build date and prints `Falling back to "2025-10-11"` on every test
  run. That warning is local only; the deployed Worker honours the configured date. Do not
  "fix" it by lowering the date.
- **`wrangler types` only sees bindings declared in `wrangler.jsonc`.** Secrets are not
  declared there, so `BOARD_TOKEN` reaches the generated `Env` only because it is listed in
  `worker/.dev.vars`, which is gitignored. On a fresh clone, `npm --prefix worker test` fails
  to type-check until you create that file. Its value is a local dev token and has nothing to
  do with the real secret.
- **npm blocks postinstall scripts by default here.** A fresh `npm install` in `worker/`
  leaves `workerd` and `esbuild` without their binaries, and every test fails confusingly.
  Run `npm install-scripts approve workerd esbuild` once, then install again.
