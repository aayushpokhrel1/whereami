---
name: wipboard
description: The board for the repos you forgot about, read on a phone.
colors:
  surface-page: "#fafafa"
  surface-card: "#ffffff"
  ink: "#1a1a1a"
  ink-muted: "#57606a"
  border: "#d0d7de"
  chip: "#eaeef2"
  fresh: "#1a7f37"
  warn: "#9a6700"
  alarm: "#b42318"
  alarm-wash: "#fff5f4"
  surface-page-dark: "#0d1117"
  surface-card-dark: "#161b22"
  ink-dark: "#e6edf3"
  ink-muted-dark: "#8b949e"
  border-dark: "#30363d"
  chip-dark: "#21262d"
  fresh-dark: "#3fb950"
  warn-dark: "#e3b341"
  alarm-dark: "#ff7b72"
  alarm-wash-dark: "#2d1618"
typography:
  display:
    fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.6rem"
    fontWeight: 700
    lineHeight: 1.45
    letterSpacing: "normal"
  headline:
    fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 700
    lineHeight: 1.45
    letterSpacing: "0.02em"
  title:
    fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "normal"
  body:
    fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
  label:
    fontFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0.04em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
rounded:
  sm: "4px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.4rem"
  md: "0.6rem"
  lg: "1rem"
  xl: "1.5rem"
components:
  card-row:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.6rem 0.7rem"
  card-row-suspect:
    backgroundColor: "{colors.alarm-wash}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0.6rem 0.7rem"
  chip-stage:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.1rem 0.45rem"
  flag:
    textColor: "{colors.alarm}"
    typography: "{typography.label}"
  age-fresh:
    textColor: "{colors.fresh}"
    typography: "{typography.display}"
  age-warn:
    textColor: "{colors.warn}"
    typography: "{typography.display}"
  age-stale:
    textColor: "{colors.alarm}"
    typography: "{typography.display}"
  empty-panel:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "1rem"
  code-inline:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.ink}"
    typography: "{typography.mono}"
    rounded: "{rounded.sm}"
    padding: "0.1rem 0.3rem"
---

# Design System: wipboard

## Overview

**Creative North Star: "The Shop Door Board"**

This is the board nailed up by the door of a workshop, read on the way past. Nobody stands
in front of it. They glance, take one fact away, and keep walking. Everything here follows
from that: the oldest thing on the page is the biggest, the states that matter shout in a
single word, and there is nothing to linger over because lingering was never the job.

The page descends from a terminal table and does not pretend otherwise. It is flat, system
fonts, bordered rectangles, no imagery, no illustration, no empty decoration. What makes it
feel designed rather than unstyled is the hierarchy: one enormous number at the top (how old
this snapshot is), then a list of cards whose only ornament is a thick red edge on the rows
that are lying to you. The restraint is load-bearing, not an absence of effort. A board that
looked expensive would be a board you distrust.

It is read on a phone, usually in the dark, usually one-handed, usually for about four
seconds. The dark scheme is not a courtesy, it is the common case. Single column is the base
layout and the wide layout is the afterthought, which is the reverse of how most pages are
built here.

**Key Characteristics:**

- One number dominates the page, and it is a confession, not a metric.
- Flat surfaces, 1px borders, zero shadows.
- System fonts only. Monospace appears exactly where the content is machine text.
- Red is reserved. When it appears, something is wrong.
- Dark mode is a first-class scheme, not an inversion.
- No motion anywhere. Nothing animates, transitions, or fades.

## Colors

A muted developer-tool palette: near-greys for everything structural, and three saturated
tones used only to state a condition.

### Primary

- **Alarm Red** (`#b42318` light / `#ff7b72` dark): the only insistent colour in the system.
  It carries the stale snapshot age, the `!` suspect flag, and the 6px left edge of a suspect
  row. It is the product's whole thesis rendered as a hue, so it must stay rare.
- **Fresh Green** (`#1a7f37` light / `#3fb950` dark): the snapshot age when it is under an
  hour. Appears at most once per page.
- **Amber Warn** (`#9a6700` light / `#e3b341` dark): the snapshot age between one hour and a
  day. Also at most once per page.

### Neutral

- **Paper** (`#fafafa` light / `#0d1117` dark): the page behind the cards.
- **Card** (`#ffffff` light / `#161b22` dark): every row and the empty panel, lifted off the
  page by tone alone.
- **Ink** (`#1a1a1a` light / `#e6edf3` dark): body text and project names.
- **Muted Ink** (`#57606a` light / `#8b949e` dark): the stage label, the metadata row, the
  host line, the git line. Everything that is context rather than content.
- **Hairline** (`#d0d7de` light / `#30363d` dark): the 1px card border and the dashed border
  of the empty panel.
- **Chip Grey** (`#eaeef2` light / `#21262d` dark): the stage-count pills and inline `code`.
- **Alarm Wash** (`#fff5f4` light / `#2d1618` dark): the background of a suspect row, a tint
  of Alarm Red at the lowest strength that still reads as different.

### Named Rules

**The Three Tones Rule.** Red, green and amber are condition colours. They may only ever
report a state the data actually holds: snapshot freshness and the suspect flag. They are
never used for emphasis, branding, links, headings, or because a region needed livening up.
On a healthy board the page is entirely grey, and that is correct.

**The Inherited Palette Rule.** These values came from GitHub's interface, not from a
decision. The *roles* are binding: three distinguishable freshness tones, one alarm colour,
one muted tier for context, one hairline, one chip fill. The *hex values* are the current
implementation and a future pass may replace them, provided it keeps the roles and clears
WCAG 2.2 AA. Do not treat `#b42318` as sacred; do treat "there is exactly one alarm colour"
as sacred. (Asked and decided on 2026-10-31: the author had no attachment to the specific
hexes, and pinning inherited values would have put this file in the way of a future contrast
fix.)

**The No Colour Alone Rule.** Every condition colour ships with text that says the same
thing. The age tone is paired with a written note, the suspect row is paired with a 6px edge
and a bolder name, the flags are words (`!`, `stuck 41d`, `dirty`) and not swatches. Colour
is the second channel here and never the first. PRODUCT.md holds this page to WCAG 2.2 AA
and these states are the entire value of the page, so this rule is not negotiable.

## Typography

**Display Font:** none. The system UI stack carries every role.
**Body Font:** `system-ui, -apple-system, "Segoe UI", sans-serif` at 16px/1.45.
**Label/Mono Font:** `ui-monospace, SFMono-Regular, Menlo, monospace`.

**Character:** deliberately anonymous. The page borrows whatever the phone already uses, so it
reads as part of the device rather than as a site. The entire hierarchy is built from two
families, five sizes and three weights, which is the smallest vocabulary that still produces
a scannable page.

### Hierarchy

- **Display** (700, 1.6rem): the snapshot age, and nothing else. It is the largest thing on
  the page by a wide margin, which is the single most important design decision here.
- **Headline** (700, 1.1rem, 0.02em): the `wipboard` wordmark in the header. Deliberately
  smaller than the age beneath it.
- **Title** (600, 1.05rem): a project name. Rises to 700 on a suspect row.
- **Body** (400, 16px, 1.45): the freeform note, and the prose in the empty and
  version-mismatch panels.
- **Label** (400, 0.8rem, 0.04em, uppercase for the stage): the stage name, the stage-count
  chips, the git line. Metadata sits at 0.85rem, one step above the smallest.
- **Mono** (400, 0.8rem): the branch name and inline `code` in panel copy. Machine text only.

### Named Rules

**The Age Outranks The Name Rule.** The snapshot age is set larger than the product's own
wordmark and larger than every project on the board. A visitor who reads one thing must read
how old this page is, because a dashboard that silently shows yesterday is the exact failure
this project exists to prevent. Never let another element outgrow it.

**The Monospace Means Machine Rule.** Monospace marks text the machine produced or the reader
must type: a branch name, a command. A project name is a human name and stays in the UI face
even though a terminal would have set it in mono.

## Layout

Single column, `1rem` of page padding, cards in a `0.6rem` grid gap. The only breakpoint is
`40rem`, where padding grows to `1.5rem`, the gap to `0.75rem`, card padding to
`0.75rem 1rem`, and the body is capped at `52rem` and centred. There is no multi-column
layout at any width: a second column would turn a glance into a search.

Each row is a four-part stack: a head (name left, stage right, baseline-aligned, pushed apart
with `justify-content: space-between`), a wrapping metadata line, an optional note paragraph,
and a wrapping git line. Every horizontal group is a flex row with `flex-wrap: wrap` and a
`0.4rem` gap, so nothing ever overflows a narrow screen.

Long strings get `overflow-wrap: anywhere` on the project name, the note and the commit
subject. These are arbitrary user text and a 40-character repo name must break rather than
push the card wide.

Spacing runs on a small, mostly quarter-rem scale: `0.2`, `0.25`, `0.3`, `0.4`, `0.6`, `0.7`,
`0.75`, `1`, `1.5rem`. It is tight on purpose. The page is a list to be scanned, not a
document to be read.

### Named Rules

**The One Column Rule.** The phone is the design target and the wide screen is the
accommodation. Build and check the narrow layout first; the `40rem` block may only adjust
padding, gap and measure, never introduce a new arrangement.

## Elevation & Depth

Flat. There is no `box-shadow` anywhere in the stylesheet. A card separates from the page by
tone (white on `#fafafa`, `#161b22` on `#0d1117`) plus a 1px hairline border, and that is the
whole depth model. The empty panel uses the same border dashed rather than solid, which is
the only variation in the system.

This is recorded as the current state, not an invariant: the author chose "flat now, shadows
allowed later" on 2026-10-31. A future pass may introduce elevation, but it inherits one
constraint from the colour system, that depth must not become a second way of signalling
condition. The suspect row is marked by its red edge, never by sitting higher.

## Shapes

Rectangles with gently rounded corners. Three radii and no more: `8px` on cards and panels,
`4px` on inline code, and a full `999px` pill on the stage-count chips. Borders are always
1px and always the hairline colour, with one exception that carries meaning: the 6px solid
`border-left` on a suspect row, the only heavy stroke in the system.

### Named Rules

**The Thick Edge Means Suspect Rule.** A 6px left border is reserved for a row whose stage
may be a lie. No other element may take a border wider than 1px, or the one signal that
matters stops being visible at a glance.

## Components

### Card Rows

- **Shape:** `8px` corners, 1px hairline border.
- **Default:** card background, `0.6rem 0.7rem` padding, rising to `0.75rem 1rem` above
  `40rem`.
- **Suspect:** alarm-wash background, a 6px solid alarm-red `border-left`, and the project
  name at 700 instead of 600. Three simultaneous signals, only one of which is colour.
- **States:** none. The rows are not interactive, have no hover, and contain no links.

### Stage Chips

- **Style:** pill (`999px`), chip-grey fill, label type, `0.1rem 0.45rem` padding, in a
  wrapping `0.4rem` flex row under the header.
- **Content:** a stage name and its count (`building 6`). Counts only, never filters: the page
  is read-only.

### Flags

- **Style:** 700 weight in alarm red, inline in the metadata row, space separated.
- **Content:** the literal CLI flags (`!`, `stuck 41d`, `dirty`, `^3`). The dashboard and the
  terminal use the same words so the two views never need translating.

### The Age Header

The signature component. A wordmark at 1.1rem, then the age at 1.6rem/700 in one of three
tones, then a plain-language note when the news is bad, then the hostname at 0.85rem muted.

- **Fresh** (under 1 hour): green, no note.
- **Warn** (1 to 24 hours): amber, note reads "The snapshot is getting old."
- **Stale** (over 24 hours, or an unreadable timestamp): red, note at 600 weight.

The tone and the note are produced together by `snapshotAge` in `worker/src/render.ts`, which
carries a comment saying why. Never render the tone without its note.

### Empty and Mismatch Panels

- **Style:** card background, 1px *dashed* hairline border, `8px` corners, `1rem` padding.
- **Use:** nothing pushed yet, or a payload version the Worker does not understand. Both lead
  with the age header styling so the page shape never changes, and both state the exact
  command that fixes it in inline `code`.

## Do's and Don'ts

### Do:

- **Do** keep the snapshot age the largest element on the page (1.6rem/700), larger than the
  wordmark and every project name.
- **Do** pair every condition colour with words. The tone is the second channel, never the
  only one.
- **Do** design the narrow layout first and treat the `40rem` block as padding and measure
  only.
- **Do** give dark mode equal care. It is the common case, read on a phone at night, and every
  condition colour has a separate dark value for contrast reasons.
- **Do** use the CLI's exact flag strings (`!`, `stuck Nd`, `dirty`, `^N`) so the two views
  never disagree.
- **Do** keep the whole stylesheet inline in `render.ts`. No build step, no framework, no
  client-side fetch: the page must work with nothing but the HTML that arrives.

### Don't:

- **Don't** use red, green or amber for anything that is not a reported condition. No red
  headings, no green buttons, no amber highlights.
- **Don't** add a second column at any width.
- **Don't** add motion. There is not one transition, animation or fade in the system, and a
  page read for four seconds has nothing to animate.
- **Don't** introduce a border heavier than 1px except the suspect row's 6px left edge.
- **Don't** add a fourth radius, a third font family, or a colour that does not have a role
  listed above.
- **Don't** make anything interactive. The dashboard is read-only by product decision; a
  button here implies a write path that does not exist.
- **Don't** interpolate a value into the markup without `escapeHtml`. Project names and notes
  are user text read in a browser, and the rule lives as a comment at that function.
