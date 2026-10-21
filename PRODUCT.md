# Product

## The problem

A developer with twenty side projects knows the state of two of them. The rest are a folder
of repos whose last commit could be yesterday or last March, half of them with uncommitted
work, several finished but never marked finished, a couple abandoned for a reason nobody
wrote down.

Every tool that addresses this (Notion boards, GitHub Projects, Linear, Trello) asks the
developer to enter status by hand. That is the exact action they have already proven they
will not do. A tracker you have to remember to update becomes one more project you forget
to update.

## The insight

Most of what you want to know is already on disk. Git knows when each repo last moved,
which branch it is on, whether there is uncommitted work, whether anything is unpushed.
None of that needs typing.

Exactly one field needs a human: which cycle the project is in. "Last commit was 3 days ago"
does not distinguish a project in design from one in testing from one that shipped.

So: derive everything derivable, ask for the one field that is left, and use the derived data
to catch the hand-written field lying. That last part is the product. When a repo has commits
newer than its stage, the board marks itself suspect.

## Who it is for

A solo developer or a small team with more repos than attention, working locally, who would
rather run one command than maintain a board. Not for project management, not for teams
tracking each other's work, not for anything with tickets.

## Decisions

- **Fixed stage vocabulary plus a freeform note.** Fixed stages let the tool sort by cycle,
  reject typos, and detect "building for six weeks". A freeform note holds what a stage name
  cannot ("waiting on an API key", "half-migrated"). Freeform-only was considered and
  rejected: it is more honest about messy states but reduces the board to sorting by date,
  which git already does.
- **The store lives at user level**, `~/.config/wipboard/projects.json`, not in any repo.
  A tool must not write into its own install directory, and the board spans repos.
- **The roots list lives in the store**, so there is no separate config file to go stale.
- **Nothing runs in the background.** An early design stamped activity into the store from a
  git `post-commit` hook. That was deleted before it was built: reading `git log` at display
  time gives the same answer with no hook, no write contention, and no possibility of drift.

## Deferred, and why

- ~~**A web UI or hosted dashboard.**~~ **Built on 2026-10-20**, and this entry is kept
  rather than deleted because the reason it changed matters. The deferral named its own
  revisit condition, "only if multi-machine becomes real", and reading the board from a
  phone is that condition. What was actually wrong with the original reasoning: it treated
  "dashboard" and "server to maintain" as the same thing. They are not. The Worker holds one
  KV key and no git knowledge, so there is no second source of truth, only a second view.

  The cost that *was* real is unavoidable and is now paid openly: a Worker cannot read the
  machine's repos, so the page is a snapshot and can be stale, which is the one property the
  CLI was built to eliminate. The design's answer is that the page states its own age. See
  `docs/superpowers/specs/2026-10-20-live-dashboard-design.md`.
- **Per-project history and trend data.** Appealing and useless until there is a question it
  answers. Add when someone asks "how long does a project sit in testing". Every push
  overwrites the single KV key, so the dashboard did not sneak history in.
- **A second machine writing to the board.** One key, one writer. The payload already carries
  `host`, so a per-host key and a merged view is an additive change, but nothing is built for
  it until a second machine exists.
- **Editing stages from the dashboard.** Read-only. A write path needs real per-user auth
  rather than one shared token, and the CLI is already where stages change.
- **Remote providers (GitHub issues, PR counts, CI status).** Needs network, auth, and rate
  limits for information that does not change which project you pick up today.
- **`remove` and `rename` commands.** `init` rescans, and the store is readable JSON.
