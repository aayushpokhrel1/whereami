---
description: Show the project board, or move a project to a new stage.
---

Run `whereami` to print the board, then answer the user's question from that output.

With arguments:
- A stage change ("move Budgerr to spec", "Budgerr -> spec") runs
  `whereami set <project> <stage>`, adding `--note "..."` when the user gave one.
- A question ("what is stale", "what did I abandon", "what has uncommitted work") is answered
  from the board output. Do not guess at projects that are not on it.

Stages are exactly: idea, spec, building, testing, shipped, parked.

A `!` flag means that project has commits newer than its last stage change, so its stage is
suspect. Those are the rows worth mentioning first, unprompted: they are what the tool is for.

Arguments: $ARGUMENTS
