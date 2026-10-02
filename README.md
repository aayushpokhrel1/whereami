# whereami

A board for the repos you forgot about.

Every other project tracker asks you to type your status in. This one reads it out of git.
Branch, last commit, uncommitted work, unpushed commits: all derived on every run, so the
board physically cannot be stale about activity. The only thing you ever type is the one
field a machine cannot infer, which cycle a project is in.

> **Status: pre-release.** Not yet published to PyPI. Install from source (see below).

```
PROJECT                  STAGE      TOUCHED   NOTE
FamilyRecipes            building      21m
Delegation Pipeline      shipped       12h     ! moved since stage set
Chess_Coach              testing        5d     dirty
Research_DNA             spec           5d     stuck 41d
Budgerr                  idea            -     no git
```

## Install

```bash
uv tool install whereami        # once published
pipx install whereami           # or this
```

From source:

```bash
git clone https://github.com/aayushpokhrel1/whereami && cd whereami && uv tool install .
```

Python 3.11+. No dependencies, standard library only.

## Use

```bash
whereami init ~/code            # register a folder of repos, discover them one level deep
whereami                        # the board, stalest first
whereami set Budgerr spec --note "waiting on an API key"
whereami md PROJECTS.md         # write a markdown board for GitHub or your phone
```

Stages are fixed: `idea spec building testing shipped parked`. The freeform `--note` holds
the messy truth that a stage name cannot.

## The three flags

| Flag | Means |
| --- | --- |
| `!` | The repo has commits newer than the last stage change. The stage you are reading may be a lie. |
| `stuck Nd` | The stage has not changed in over 30 days while commits kept landing. |
| `dirty` / `^N` | Uncommitted or unpushed work, the kind that actually gets lost. |

The `!` flag is the point of the tool. A board you have to remember to update is a board
that lies to you; this one tells you when it is lying.

## Make it unavoidable

The board is only useful if you see it without choosing to. Add it to your shell profile:

```bash
alias projects=whereami
```

Claude Code users: the repo is also a plugin, so `/whereami` reads and updates the board
mid-conversation. See [docs/OPERATIONS.md](docs/OPERATIONS.md) for a `SessionStart` hook that
prints the board every time you open a session.

## Where things are written down

| File | What it holds |
| --- | --- |
| `README.md` | This file: what it is, install, usage |
| `PRODUCT.md` | Who it is for, decisions, what is deferred and why |
| `docs/OPERATIONS.md` | Run, verify, release, hook setup, environment traps |
| `docs/superpowers/specs/` | The design of one feature, written before building it |
| `CLAUDE.md` | How to work in this repo |

## Licence

MIT.
