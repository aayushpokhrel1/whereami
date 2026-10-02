# whereami: design

**Date:** 2026-10-02
**Status:** approved, not yet built

## Problem

Eighteen project folders on one machine, and no single view of which cycle each one is in.
The state is not missing: fourteen are git repos with commit history, seven carry a
`HANDOVER.md` describing current state, every one has a `CLAUDE.md`. What is missing is one
place to see it all, and a reason to believe what that place says.

Every tracker considered (GitHub Projects, Notion, Linear, an Obsidian Dataview board) fails
the same way: it asks for status to be entered by hand, which is the action already proven
not to happen. A board you must remember to update becomes the nineteenth forgotten project.

## Approach

Derive everything git can answer. Ask for the one field it cannot. Use the derived data to
catch the hand-written field lying.

Derived on every run, never stored:

- current branch
- time since last commit
- uncommitted changes present
- commits not pushed to upstream

Stored, because no tool can infer it:

- `stage`, from a fixed vocabulary
- `note`, freeform
- `stage_set_at`, the timestamp of the last stage change

Because activity is derived at display time, the board cannot be stale about activity. There
is no sync step and no background process.

## Store

`~/.config/whereami/projects.json`, on every platform. User level, not inside any repo: the
board spans repos and a tool must not write into its own install directory.

```json
{
  "roots": ["C:/Users/aayus/dev/Projects"],
  "projects": {
    "FamilyRecipes": {
      "stage": "building",
      "note": "recipe import half-migrated",
      "stage_set_at": "2026-10-02T14:20:00"
    }
  }
}
```

The roots list lives in the store, so there is no second config file to drift. Project keys
are folder names; the path is reconstructed by joining a root, so moving a root does not
orphan the stage data for the projects under it.

Projects discovered under a root but absent from `projects` default to stage `idea` with no
note. A project in the store whose folder has disappeared is shown as `missing` rather than
dropped, because silently losing a row is how a board loses trust.

## Commands

| Command | Behaviour |
| --- | --- |
| `whereami` | Same as `show` |
| `whereami show` | Print the board, stalest first |
| `whereami init [path]` | Register `path` (default: cwd) as a root, discover child folders one level deep |
| `whereami set <project> <stage> [--note TEXT]` | Set stage, stamp `stage_set_at`, optionally set the note |
| `whereami md <file>` | Write the board as a markdown table |

Stages, exactly: `idea spec building testing shipped parked`. An invalid stage exits non-zero
and prints the valid list. `set` on an unknown project exits non-zero rather than creating a
row, since the usual cause is a typo in the project name.

`md` writes a view, not a store. It is regenerated and never hand-edited.

## Flags

Three, computed at display time:

- **`!`** last commit is newer than `stage_set_at`. The stage on screen may be a lie. This is
  the whole point of the tool: the board reports its own suspect rows.
- **`stuck Nd`** `stage_set_at` is more than 30 days old while commits have landed since. A
  project that has been "building" for six weeks is a different problem from an idle one.
- **`dirty`** uncommitted changes, **`^N`** N commits unpushed. Work that can actually be lost.

A folder with no `.git` shows `-` for activity and `no git` as a flag. It carries no `!`,
since there is no commit to compare against. Three of the eighteen target folders are in this
state, so it is a normal case, not an error path.

## Sort

Stalest first, by time since last commit, descending. Rows carrying `!` are hoisted to the
top regardless of age: a suspect row is the one worth acting on. `parked` rows sort after
everything active, since they are deliberately idle and should not dominate the board, and
`no git` rows sort last, since there is no signal to rank them by.

## Error handling

- Any `git` invocation that fails for any reason yields "no git" for that project. Nothing in
  the board is important enough to raise on.
- `git` missing from PATH degrades every row to "no git". The board is useless but does not
  crash, and the condition is visible rather than silent.
- A missing store means a first run: `show` prints a one-line hint to run `init`, exits zero.
- A corrupt store exits non-zero naming the file, and does not overwrite it. Losing the one
  hand-entered field in the system to an automatic repair would be worse than stopping.
- Every write rewrites the file whole. Two concurrent `set` calls can lose one. Acceptable for
  a single-user tool, documented in operations.

## Testing

`test_whereami.py`, standard library plus pytest, no fixtures beyond a temp directory. It
builds real throwaway git repos and commits to them, because the logic under test is entirely
about reading git.

Covered:

1. **The `!` flag fires** when a commit lands after `stage_set_at`, and does not fire when the
   stage was set after the last commit. This is the most important test in the repo: if the
   flag silently stops working, the tool becomes a worse `ls` and nothing else notices.
2. **A folder with no `.git`** appears with `no git`, carries no `!`, and does not raise.
3. **Sort order** puts a suspect row above an older quiet row.
4. **An invalid stage** exits non-zero without modifying the store.
5. **`set` stamps `stage_set_at`**, which is the hinge every flag depends on.

## Distribution

Single module `whereami.py`, packaged with hatchling, console script `whereami`. Python 3.11+,
standard library only, no dependencies: a one-line install for a stranger, and a tool that
prints a table does not need a dependency tree.

The repo doubles as a Claude Code plugin (`.claude-plugin/plugin.json` plus
`commands/whereami.md`) so the board is readable and editable mid-conversation. The plugin is
a thin wrapper over the CLI and carries no logic of its own.

## Deliberately excluded

- **Any background process.** An earlier draft stamped activity into the store from a git
  `post-commit` hook. Deleted before being built: reading `git log` at display time gives the
  same answer with no hook, no write contention, and no drift.
- **A web UI or server.** The data is in folders on one machine. `md` plus a pushed repo gives
  a phone-readable board for free.
- **Per-project history**, remote providers, `remove` and `rename`. See `PRODUCT.md` for why
  each is deferred.
