export interface Job {
  _id: string;
  dedup_key: string;
  active: boolean;
  ats: string;
  company: string;
  first_seen: string;
  last_seen: string;
  location: string;
  posted_date: string | null;
  role_category: string;
  seniority: string;
  sources: string[];
  tech: string;
  title: string;
  url: string;
  source: string;
}

export interface Bucket {
  _id: string;
  n: number;
}

export interface Stats {
  total: number;
  porSeniority: Bucket[];
  porRol: Bucket[];
  porFuente: Bucket[];
  recientes: { _id: string; n: number }[];
  actualizado: string | null;
}

export interface CompanySignal {
  empresa: string;
  activas: number;
  nuevas: number;
  senior: number;
  areas: { area: string; n: number; nuevas: number }[];
}

export interface JobsParams {
  company?: string;
  role?: string;
  seniority?: string;
  source?: string;
  q?: string;
  days?: number;
  limit?: number;
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export function fetchStats(): Promise<Stats> {
  return getJSON<Stats>("/api/stats");
}

export function fetchCompanies(days = 7): Promise<CompanySignal[]> {
  return getJSON<CompanySignal[]>(`/api/companies?days=${days}`);
}

export function fetchJobs(params: JobsParams): Promise<Job[]> {
  const sp = new URLSearchParams();
  if (params.role && params.role !== "all") sp.set("role", params.role);
  if (params.seniority && params.seniority !== "all")
    sp.set("seniority", params.seniority);
  if (params.source && params.source !== "all") sp.set("source", params.source);
  if (params.company) sp.set("company", params.company);
  if (params.q) sp.set("q", params.q);
  if (params.days) sp.set("days", String(params.days));
  sp.set("limit", String(params.limit ?? 100));
  return getJSON<Job[]>(`/api/jobs?${sp.toString()}`);
}