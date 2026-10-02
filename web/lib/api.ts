export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T = Record<string, unknown>>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/${path.replace(/^\//, "")}`, {
    ...options,
    headers: { "content-type": "application/json", ...options.headers },
    cache: "no-store",
  });
  if (response.status === 204) return undefined as T;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail || payload.message || "Something went wrong. Please try again.";
    throw new ApiError(String(message), response.status);
  }
  return payload as T;
}

export type User = { id: number; name: string; email: string; created_at: string };
export type Task = {
  id: number;
  user_id: number;
  title: string;
  description?: string | null;
  category?: string | null;
  status: "backlog" | "in_progress" | "blocked" | "completed";
  priority: "low" | "medium" | "high";
  due_date?: string | null;
  estimated_minutes?: number | null;
  urgent: boolean | number;
  overdue?: boolean;
  created_at: string;
  updated_at: string;
};

export const STATUSES: Task["status"][] = ["backlog", "in_progress", "blocked", "completed"];
export const STATUS_LABELS: Record<Task["status"], string> = {
  backlog: "Backlog",
  in_progress: "In progress",
  blocked: "Blocked",
  completed: "Completed",
};
export const PRIORITY_CLASS: Record<Task["priority"], string> = {
  low: "pill-green",
  medium: "pill-blue",
  high: "pill-orange",
};
export function formatDate(value?: string | null) {
  if (!value) return "No date";
  const parsed = new Date(`${value.slice(0, 10)}T12:00:00`);
  return Number.isNaN(parsed.getTime()) ? value : new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(parsed);
}
export function relativeTime(value?: string) {
  if (!value) return "";
  const date = new Date(value.replace(" ", "T") + (value.endsWith("Z") ? "" : "Z"));
  const minutes = Math.round((date.getTime() - Date.now()) / 60000);
  const formatter = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  if (Math.abs(minutes) < 60) return formatter.format(minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return formatter.format(hours, "hour");
  return formatter.format(Math.round(hours / 24), "day");
}
