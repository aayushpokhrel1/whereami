# Live dashboard: design

**Date:** 2026-10-20
**Status:** approved, not yet built

## Problem

The board exists only as a terminal table on one machine. The requirement is to read it from
a phone, including when that machine is off, and to have it be current when the machine is on.

`PRODUCT.md` deferred a web UI with an explicit revisit condition: *"Revisit only if
multi-machine becomes real."* Phone access is that condition. This supersedes the deferral,
and `PRODUCT.md` must be corrected rather than left to contradict this document.

## Constraint that shapes everything

A Worker runs in Cloudflare's network and cannot read `~/dev/Projects`. Nothing deployed to
Cloudflare can derive the board. The machine holding the repos must push.

That reintroduces the one property the CLI was designed to avoid: the dashboard can be stale.
The design does not hide this. It pushes on real events so the window is small, and it prints
the snapshot's age on the page, in the same spirit as the `!` flag. A dashboard that says
"as of 4 minutes ago" is truthful. One that silently shows yesterday is the failure this
project exists to prevent.

## Architecture

```
this machine                          Cloudflare
------------                          ----------
wipboard push ---POST /api/board--->  Worker ---> KV  (one key, one JSON blob)
  bearer token                          |
                                        v
phone ---GET / ---> Access (email) --> Worker renders HTML, "as of 4m ago"
```

One Worker, one KV namespace, one key. No database, no per-request fan-out, no tunnel.

## Data contract

`wipboard push` serializes the output of `build_rows` and posts it. The Worker has no git
knowledge and never parses a repo; it stores and renders whatever it is given.

```json
{
  "version": 1,
  "generated_at": "2026-10-20T15:31:00",
  "host": "DESKTOP-ABC",
  "projects": [
    {
      "name": "FamilyRecipes",
      "stage": "building",
      "note": "live in production, feature work ongoing",
      "last_commit": "2026-10-20T15:28:11",
      "stage_set_at": "2026-10-02T02:19:00",
      "flags": ["!", "dirty", "^4"],
      "has_git": true,
      "branch": "master",
      "subject": "Add remedies and appeals",
      "changed": 3
    }
  ]
}
```

`version` is present so a future change to the shape can be detected rather than guessed at.
The Worker rejects a payload whose `version` it does not know, with 400.

All timestamps are naive UTC ISO strings, matching the store. The Worker treats them as UTC.

## New derived fields

Three additions to `git_info`, used by the dashboard and harmless to the terminal table:

- `branch`: already derived, currently unused in output.
- `subject`: the last commit message subject. It must NOT be a second `git log` call. The
  existing call becomes `git log -1 --format=%cI%n%s` and the output is split on the first
  newline, so the number of processes spawned per repo is unchanged. Twenty repos times an
  extra process spawn is a cost paid on every single run, on the platform where spawning is
  most expensive.
- `changed`: the number of lines `git status --porcelain` returns, which is the number of
  changed paths. The same call already decides `dirty`, so this adds no invocation either.

`stage_set_at` is already stored and is sent as-is so the dashboard can show time-in-stage,
which is the number that distinguishes a project resting from one stuck.

Each follows the existing rule: derived on demand, never stored, and any git failure yields
the absent case rather than raising.

## Worker

**Routes**

| Route | Behaviour |
| --- | --- |
| `POST /api/board` | Validate bearer token, validate payload, write KV, return 204 |
| `GET /` | Read KV, render the dashboard HTML, return 200 |
| anything else | 404 |

**Auth.** `POST` requires `Authorization: Bearer <token>`. The token is a Worker secret
(`BOARD_TOKEN`), set with `wrangler secret put`, never in `wrangler.jsonc` and never in the
repo. Comparison uses `crypto.subtle.timingSafeEqual` over SHA-256 digests of both values, so
neither the token nor its length leaks through timing. A direct `===` is not acceptable here.

`GET /` is protected by Cloudflare Access with an email policy, because the board is a
complete private project list with candid notes. Access cannot guard the push, since a
scheduled task cannot complete an email login, so the Access application covers `/` only and
a bypass policy exempts `/api/board`. The bearer token is what protects that path.

**Payload bound.** The body is read with `await request.json()`, which is safe only because
the payload is bounded. The Worker rejects any request with `Content-Length` over 1 MiB with
413 before reading the body, so the buffering stays bounded by contract rather than by hope.
A twenty-project board is a few kilobytes.

**Storage.** One KV key, `board:current`, overwritten on every push. KV reads are eventually
consistent and can lag up to roughly a minute globally, which is well inside the staleness
the page already advertises. No TTL: the last known state is the point when the laptop is off.

**Config.** `compatibility_date` set to the build date, `workers_dev: true`, name `wipboard`.
`observability.enabled` and `observability.traces.enabled` both true; the top-level setting
alone does not enable traces. The `Env` type is generated with `wrangler types`, not
hand-written, so it cannot drift from the bindings.

## The page

Server-rendered HTML from the Worker. No framework, no build step, no client-side fetch. It is
read on a phone, so it is designed narrow-first and widens on larger screens.

**Header** carries the snapshot age, and this is the most important element on the page:
under an hour reads normally, over an hour is amber, over a day is red and says the machine
has probably been off. Also a count per stage.

**Rows** carry everything the terminal shows (stage, touched, flags, note) plus branch,
last commit subject, changed-file count, and time-in-stage. Suspect rows (`!`) keep the same
hoist and the same visual weight they have in the terminal: the two views must not disagree
about what matters.

Sorting matches `_sort_key` exactly. Two views of one board that order rows differently would
be worse than having one view.

## wipboard push

```
wipboard push          # posts the current board, prints the endpoint and the row count
```

Reads `endpoint` and `token` from `~/.config/wipboard/config.json`, with `WIPBOARD_ENDPOINT`
and `WIPBOARD_TOKEN` taking precedence so a scheduled task can pass them without a file.

Missing configuration exits 2 naming what is absent and how to set it. A network failure or a
non-2xx response exits 2 printing the status, and never touches the store. `push` is strictly
read-only with respect to local state.

This is the first part of the tool that makes a network call, so it is also the first that can
hang. It uses a 10 second timeout and treats a timeout as an ordinary failure.

**Triggers**, so freshness follows events rather than a clock:

1. The existing user-global `post-commit` hook, so any commit in any repo pushes within
   seconds. This is the trigger that matters, because a commit is what makes a stage suspect.
2. After a successful `wipboard set`, so a stage change is visible immediately.
3. A Windows Scheduled Task every 15 minutes, which catches dirty trees and elapsed time.

Each trigger is documented in `docs/OPERATIONS.md` and none is installed automatically. A tool
that edits a stranger's git hooks on install would be a bad citizen, the same reasoning that
kept the `SessionStart` hook out of the repo.

## Error handling

- Push with no config, bad config, unreachable endpoint, timeout, or non-2xx: exit 2, message
  naming the cause, local store untouched.
- Worker with a missing or wrong bearer token: 401, no detail about why.
- Worker with an unknown `version` or malformed payload: 400, naming the field.
- Worker with an oversized body: 413 before reading.
- `GET /` with an empty KV: a page saying no board has been pushed yet, with the command to
  run. Not an error, and not a blank screen.

## Testing

**Python side**, in the existing suite, no network:

1. `push` with no configuration exits 2 and does not write the store.
2. The serializer produces the documented shape from a known set of rows, including a row with
   no git, with `version` and every documented key present. This is the contract the Worker
   depends on, so it is the test that matters most on this side.

**Worker side**, Vitest with `@cloudflare/vitest-pool-workers`, running in the real runtime:

3. `POST` without a token, and with a wrong token, both return 401 and leave KV untouched.
4. `POST` with the right token stores the payload and returns 204.
5. `POST` with an unknown `version` returns 400.
6. `GET /` with a stored board renders every project name, and shows an age.
7. `GET /` with an empty KV renders the empty state rather than throwing.

The Worker's dev dependencies do not change the CLI's zero-dependency claim, but the README
badge must be reworded to say the CLI has no dependencies, so the claim stays exactly true.

## Deploy

`npx wrangler deploy` from the repo. The account is the one already used for FamilyRecipes;
this machine has no local wrangler login yet, so a one-time `npx wrangler login` is required.
The KV namespace is created once with `wrangler kv namespace create`, and the Access
application and its bypass policy are configured once in the Zero Trust dashboard. All of it
is written down in `docs/OPERATIONS.md`, including how to rotate `BOARD_TOKEN`.

**Corrected 2026-10-21:** the hostname is `wipboard.enamelvault.com`, not workers.dev, and
`workers_dev` is false. Cloudflare Access is defined against hostnames in a zone on the
account, and `workers.dev` is Cloudflare's zone, so Access cannot protect it. This document
originally specified workers.dev plus Access, which is not a combination that exists. Leaving
`workers_dev: true` alongside a custom domain would also leave an unauthenticated copy of the
board answering on the workers.dev hostname.

## Deliberately excluded

- **Any path from Cloudflare back to the machine.** A tunnel would make the board genuinely
  live, and was considered. It requires the machine awake, which is the requirement this
  design exists to drop. Adding it as a fallback would mean two systems and a failure mode on
  every request.
- **Multiple machines.** One key, one writer. A second machine would need a key per host and a
  merged view. The payload already carries `host` so that change is additive, but nothing is
  built for it until a second machine exists.
- **History and trends.** Every push overwrites. Keeping snapshots is a different product.
- **Editing stages from the page.** Read-only. A write path needs real auth on the write
  endpoint rather than a shared token, and the CLI is already the place stages change.
