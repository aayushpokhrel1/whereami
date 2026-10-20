// The dashboard is server-rendered from the KV blob. No framework, no build
// step, no client-side fetch: the page is read on a phone and must work with
// nothing but the HTML that arrives.
//
// The Worker holds no git knowledge. It renders whatever payload it is given,
// and the payload shape is owned by board_payload in wipboard.py.

export const PAYLOAD_VERSION = 1;

export interface Project {
  name: string;
  stage: string;
  note: string;
  last_commit: string | null;
  stage_set_at: string | null;
  flags: string[];
  has_git: boolean;
  branch: string;
  subject: string;
  changed: number;
}

export interface Board {
  version: number;
  generated_at: string;
  host: string;
  projects: Project[];
}

const HOUR_MS = 3600 * 1000;
const DAY_MS = 24 * HOUR_MS;

// Every interpolated value goes through this, with no exceptions. A project
// name and a note are user text read in a browser; one unescaped value is an
// injected script.
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Naive UTC ISO strings, matching the store. A trailing Z is tolerated so a
// hand-written payload does not silently read as local time.
function parseStamp(raw: string | null): number | null {
  if (!raw) return null;
  const text = /[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? raw : `${raw}Z`;
  const ms = Date.parse(text);
  return Number.isFinite(ms) ? ms : null;
}

// Largest whole unit, matching human_age in wipboard.py so the two views never
// disagree about how old something is. Clamped at zero: clock skew and a VM
// resuming from sleep must read "just now", never "-3m".
function humanAge(then: number | null, now: number): string {
  if (then === null) return "-";
  const seconds = Math.max(0, (now - then) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days <= 365) return `${days}d`;
  return `${Math.floor(days / 365)}y`;
}

// The snapshot's age is the most important element on the page: a dashboard
// that silently shows yesterday is the failure this project exists to prevent.
function snapshotAge(generatedAt: number | null, now: number): {
  text: string;
  tone: string;
  note: string;
} {
  if (generatedAt === null) {
    return { text: "unknown", tone: "stale", note: "The snapshot has no readable timestamp." };
  }
  const elapsed = Math.max(0, now - generatedAt);
  // "just now ago" is not a thing anyone says.
  const age = humanAge(generatedAt, now);
  const text = age === "just now" ? age : `${age} ago`;
  if (elapsed > DAY_MS) {
    return {
      text,
      tone: "stale",
      note: "This machine has probably been off. Nothing has been pushed since.",
    };
  }
  if (elapsed > HOUR_MS) {
    return { text, tone: "warn", note: "The snapshot is getting old." };
  }
  return { text, tone: "fresh", note: "" };
}

function stageCounts(projects: Project[]): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const project of projects) {
    counts.set(project.stage, (counts.get(project.stage) ?? 0) + 1);
  }
  return [...counts.entries()];
}

function renderRow(project: Project, now: number): string {
  const suspect = project.flags.includes("!");
  const touched = humanAge(parseStamp(project.last_commit), now);
  const inStage = humanAge(parseStamp(project.stage_set_at), now);
  const flags = project.flags
    .map((flag) => `<span class="flag">${escapeHtml(flag)}</span>`)
    .join(" ");
  const git = project.has_git
    ? `<span class="branch">${escapeHtml(project.branch || "?")}</span>
        <span class="subject">${escapeHtml(project.subject)}</span>
        <span class="changed">${escapeHtml(String(project.changed))} changed</span>`
    : `<span class="subject">no git</span>`;
  return `<li class="row${suspect ? " suspect" : ""}">
      <div class="head">
        <span class="name">${escapeHtml(project.name)}</span>
        <span class="stage">${escapeHtml(project.stage)}</span>
      </div>
      <div class="meta">
        <span class="touched">touched ${escapeHtml(touched)}</span>
        <span class="in-stage">${escapeHtml(inStage)} in stage</span>
        ${flags}
      </div>
      ${project.note ? `<p class="note">${escapeHtml(project.note)}</p>` : ""}
      <div class="git">${git}</div>
    </li>`;
}

const STYLE = `
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 1rem;
  font: 16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
  background: #fafafa;
  color: #1a1a1a;
}
header { margin-bottom: 1rem; }
h1 { font-size: 1.1rem; margin: 0 0 .25rem; letter-spacing: .02em; }
.age { font-size: 1.6rem; font-weight: 700; margin: 0; }
.age.fresh { color: #1a7f37; }
.age.warn { color: #9a6700; }
.age.stale { color: #b42318; }
.age-note { margin: .25rem 0 0; font-size: .9rem; }
.age-note.stale { color: #b42318; font-weight: 600; }
.host { margin: .25rem 0 0; font-size: .85rem; color: #57606a; }
.stages { display: flex; flex-wrap: wrap; gap: .4rem; margin: .6rem 0 0; padding: 0; list-style: none; }
.stages li { font-size: .8rem; padding: .1rem .45rem; border-radius: 999px; background: #eaeef2; }
.board { list-style: none; margin: 0; padding: 0; display: grid; gap: .6rem; }
.row { background: #fff; border: 1px solid #d0d7de; border-radius: 8px; padding: .6rem .7rem; }
.row.suspect { border-left: 6px solid #b42318; background: #fff5f4; }
.row.suspect .name { font-weight: 700; }
.head { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; }
.name { font-size: 1.05rem; font-weight: 600; overflow-wrap: anywhere; }
.stage { font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; color: #57606a; }
.meta { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .2rem; font-size: .85rem; color: #57606a; }
.flag { font-weight: 700; color: #b42318; }
.note { margin: .4rem 0 0; overflow-wrap: anywhere; }
.git { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .3rem; font-size: .8rem; color: #57606a; }
.branch { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.subject { overflow-wrap: anywhere; }
.empty { background: #fff; border: 1px dashed #d0d7de; border-radius: 8px; padding: 1rem; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #eaeef2; padding: .1rem .3rem; border-radius: 4px; }
/* This page is read on a phone, usually in the dark. */
@media (prefers-color-scheme: dark) {
  body { background: #0d1117; color: #e6edf3; }
  .age.fresh { color: #3fb950; }
  .age.warn { color: #e3b341; }
  .age.stale, .age-note.stale, .flag { color: #ff7b72; }
  .host, .stage, .meta, .git { color: #8b949e; }
  .stages li, code { background: #21262d; }
  .row { background: #161b22; border-color: #30363d; }
  .row.suspect { border-left-color: #ff7b72; background: #2d1618; }
  .empty { background: #161b22; border-color: #30363d; }
}
@media (min-width: 40rem) {
  body { padding: 1.5rem; max-width: 52rem; margin: 0 auto; }
  .board { gap: .75rem; }
  .row { padding: .75rem 1rem; }
}
`;

function page(title: string, body: string): string {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>${STYLE}</style>
</head>
<body>
${body}
</body>
</html>`;
}

export function renderBoard(payload: Board, now: Date): string {
  const nowMs = now.getTime();
  const generatedAt = parseStamp(payload.generated_at);
  const age = snapshotAge(generatedAt, nowMs);
  const stages = stageCounts(payload.projects)
    .map(([stage, count]) => `<li>${escapeHtml(stage)} ${escapeHtml(String(count))}</li>`)
    .join("");
  // Payload order is _sort_key order from the CLI. Re-sorting here would make
  // the two views disagree about what matters, which is worse than one view.
  const rows = payload.projects.map((project) => renderRow(project, nowMs)).join("\n");
  const body = `<header>
  <h1>wipboard</h1>
  <p class="age ${age.tone}">${escapeHtml(age.text)}</p>
  ${age.note ? `<p class="age-note ${age.tone}">${escapeHtml(age.note)}</p>` : ""}
  <p class="host">${escapeHtml(payload.host)}</p>
  <ul class="stages">${stages}</ul>
</header>
<ul class="board">
${rows}
</ul>`;
  return page("wipboard", body);
}

// An unknown version means the CLI was upgraded and the Worker was not. Say so
// rather than throwing or rendering half a board.
export function renderVersionMismatch(version: unknown): string {
  const body = `<header>
  <h1>wipboard</h1>
  <p class="age stale">Worker out of date</p>
  <p class="age-note stale">This Worker is older than the CLI that pushed the board.</p>
</header>
<div class="empty">
  <p>The stored payload has version ${escapeHtml(String(version))}, and this Worker only
  understands version ${escapeHtml(String(PAYLOAD_VERSION))}.</p>
  <p>Redeploy the Worker with <code>npx wrangler deploy</code> from <code>worker/</code>.</p>
</div>`;
  return page("wipboard: redeploy the Worker", body);
}

export function renderEmpty(): string {
  const body = `<header>
  <h1>wipboard</h1>
  <p class="age">No board yet</p>
</header>
<div class="empty">
  <p>Nothing has been pushed to this dashboard.</p>
  <p>Run <code>wipboard push</code> on the machine that holds the repos.</p>
</div>`;
  return page("wipboard: no board yet", body);
}
