const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "*",
  "Access-Control-Expose-Headers": "content-location",
};

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: Request) {
  const apiUrl = process.env.LANGGRAPH_API_URL;
  if (!apiUrl) {
    return Response.json(
      { error: "LANGGRAPH_API_URL is not configured" },
      { status: 500, headers: CORS_HEADERS },
    );
  }

  const incomingUrl = new URL(request.url);
  const path = incomingUrl.pathname.replace(/^\/api\/?/, "");
  incomingUrl.searchParams.delete("_path");
  incomingUrl.searchParams.delete("nxtP_path");

  const targetUrl = new URL(path, `${apiUrl.replace(/\/$/, "")}/`);
  targetUrl.search = incomingUrl.searchParams.toString();

  const headers = new Headers();
  for (const [key, value] of request.headers) {
    if (key.startsWith("x-") || key === "authorization") {
      headers.set(key, value);
    }
  }
  if (process.env.LANGSMITH_API_KEY) {
    headers.set("x-api-key", process.env.LANGSMITH_API_KEY);
  }
  if (request.headers.has("content-type")) {
    headers.set("content-type", request.headers.get("content-type")!);
  }

  try {
    const hasBody = ["POST", "PUT", "PATCH"].includes(request.method);
    const upstream = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
    });

    const responseHeaders = new Headers(upstream.headers);
    // Node fetch decodes compressed upstream bodies but retains these headers.
    // Forwarding them makes Vercel truncate JSON and event streams.
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");
    responseHeaders.delete("transfer-encoding");
    for (const [key, value] of Object.entries(CORS_HEADERS)) {
      responseHeaders.set(key, value);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Proxy request failed";
    return Response.json({ error: message }, { status: 502, headers: CORS_HEADERS });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;

export function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}
