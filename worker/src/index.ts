const MAX_BODY_BYTES = 1048576;
const PAYLOAD_VERSION = 1;
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
  // Size first, before the body is read at all.
  const declared = Number(request.headers.get("Content-Length") ?? "0");
  if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) {
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

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/api/board") {
      return ingest(request, env);
    }
    return new Response("not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;
