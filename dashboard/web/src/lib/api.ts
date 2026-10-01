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

/** Clave de cliente: llega una vez por ?key= y queda en el navegador. */
function leerClave(): string {
  try {
    const url = new URL(location.href);
    const deUrl = url.searchParams.get("key");
    if (deUrl) {
      localStorage.setItem("hs-key", deUrl);
      url.searchParams.delete("key");
      history.replaceState(null, "", url); // que no quede en capturas ni links compartidos
      return deUrl;
    }
    return localStorage.getItem("hs-key") ?? "";
  } catch {
    return "";
  }
}

const CLAVE = leerClave();

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url, CLAVE ? { headers: { "x-hs-key": CLAVE } } : undefined);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export function fetchStats(): Promise<Stats> {
  return getJSON<Stats>("/api/stats");
}

export interface CompaniesResponse {
  completo: boolean;
  total: number;
  acelerando: number;
  empresas: CompanySignal[];
}

export function fetchCompanies(days = 7): Promise<CompaniesResponse> {
  return getJSON<CompaniesResponse>(`/api/companies?days=${days}`);
}

export async function enviarLead(email: string, empresa: string): Promise<void> {
  const res = await fetch("/api/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, empresa }),
  });
  if (!res.ok) throw new Error(
      res.status === 400 ? "Revisá el email." : res.status === 429 ? "Demasiados intentos, probá en una hora." : "No pudimos enviarlo, probá de nuevo.",
    );
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