import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

type Context = { params: Promise<{ path: string[] }> };
const SESSION = "flowstate_session";

async function proxy(request: NextRequest, context: Context) {
  const { path } = await context.params;
  const endpoint = path.join("/");
  const cookieStore = await cookies();

  if (endpoint === "auth/logout") {
    cookieStore.delete(SESSION);
    return new NextResponse(null, { status: 204 });
  }

  const base = process.env.API_SERVER_URL || "http://127.0.0.1:8000/api";
  const url = new URL(`${base.replace(/\/$/, "")}/${endpoint}`);
  url.search = request.nextUrl.search;
  const headers = new Headers({ accept: "application/json" });
  const token = cookieStore.get(SESSION)?.value;
  if (token) headers.set("authorization", `Bearer ${token}`);
  if (request.headers.get("content-type")) headers.set("content-type", request.headers.get("content-type")!);

  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.text(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Flowstate API is unavailable. Start the Python API and try again." }, { status: 503 });
  }

  if (upstream.status === 204) return new NextResponse(null, { status: 204 });
  const text = await upstream.text();
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(text) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ detail: "The API returned an invalid response." }, { status: 502 });
  }

  const response = NextResponse.json(payload, { status: upstream.status });
  if (endpoint === "auth/login" && upstream.ok) {
    const data = payload.data as Record<string, unknown> | undefined;
    const sessionToken = data?.token;
    if (data && typeof sessionToken === "string") {
      response.cookies.set(SESSION, sessionToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 60 * 24,
      });
      delete data.token;
    }
  }
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
