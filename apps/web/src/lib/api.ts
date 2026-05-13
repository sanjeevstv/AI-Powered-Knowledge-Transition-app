const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("kt_token");
}

export function setToken(token: string) {
  localStorage.setItem("kt_token", token);
}

export function clearToken() {
  localStorage.removeItem("kt_token");
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token =
    path === "/auth/login" || path === "/auth/register" ? null : getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...init, headers });
  if (res.status === 401) {
    clearToken();
    throw new Error("Session expired. Please sign in again.");
  }
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function uploadDocument(file: File, tags: string) {
  const token = getToken();
  const url = new URL(`${API_BASE}/api/v1/documents`);
  url.searchParams.set("tags", tags);
  const fd = new FormData();
  fd.append("file", file);
  const headers: HeadersInit = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url.toString(), { method: "POST", headers, body: fd });
  if (res.status === 401) {
    clearToken();
    throw new Error("Session expired.");
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
