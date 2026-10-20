import { PAYLOAD_VERSION, renderBoard, renderEmpty, renderVersionMismatch } from "./render";
import type { Board } from "./render";

const MAX_BODY_BYTES = 1048576;
const BOARD_KEY = "board:current";

async function digest(value: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
}

// Constant-time comparison over fixed-length digests: never short-circuits on
// length, and never reveals how much of the token matched.
async function tokenMatches(presented: string, expected: string): Promise<boolean> {
  const [a, b] = await Promise.all([digest(presented), digest(expected)]);
  return crypto.subtle.timingSafeEqual(a, b);
}

function bearerToken(request: Request): string {
  const header = request.headers.get("Authorization") ?? "";
  const prefix = "Bearer ";
  return header.startsWith(prefix) ? header.slice(prefix.length) : "";
}

function unauthorized(): Response {
  return new Response("unauthorized", { status: 401 });
}

async function ingest(request: Request, env: Env): Promise<Response> {
  // Size first, before the body is read at all. A missing or unparseable
  // Content-Length is refused rather than defaulted: without it a chunked body
  // would reach request.text() unbounded, which is how a Worker runs out of
  // memory. The pusher always sets it.
  const header = request.headers.get("Content-Length");
  const declared = header === null ? NaN : Number(header);
  if (!Number.isFinite(declared)) {
    return new Response("length required", { status: 411 });
  }
  if (declared > MAX_BODY_BYTES) {
    return new Response("payload too large", { status: 413 });
  }

  if (!(await tokenMatches(bearerToken(request), env.BOARD_TOKEN))) {
    return unauthorized();
  }

  const body = await request.text();

  let payload: unknown;
  try {
    payload = JSON.parse(body);
  } catch {
    return new Response("invalid JSON", { status: 400 });
  }

  if (typeof payload !== "object" || payload === null) {
    return new Response("invalid payload: version", { status: 400 });
  }

  const version = (payload as { version?: unknown }).version;
  if (version !== PAYLOAD_VERSION) {
    return new Response(`unsupported payload: version must be ${PAYLOAD_VERSION}`, {
      status: 400,
    });
  }

  await env.BOARD.put(BOARD_KEY, body);
  return new Response(null, { status: 204 });
}

function html(body: string): Response {
  // The charset is explicit: without it a phone guesses, and a non-ASCII name
  // or commit subject arrives as mojibake.
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

async function dashboard(env: Env): Promise<Response> {
  const stored = await env.BOARD.get(BOARD_KEY);
  if (stored === null) {
    return html(renderEmpty());
  }

  let payload: unknown;
  try {
    payload = JSON.parse(stored);
  } catch {
    return html(renderEmpty());
  }

  // A version this Worker does not know means the CLI was upgraded and the
  // Worker was not. Say so rather than throwing or rendering half a board.
  const version = (payload as { version?: unknown } | null)?.version;
  if (version !== PAYLOAD_VERSION) {
    return html(renderVersionMismatch(version));
  }

  return html(renderBoard(payload as Board, new Date()));
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/api/board") {
      return ingest(request, env);
    }
    if (request.method === "GET" && url.pathname === "/") {
      return dashboard(env);
    }
    return new Response("not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;

