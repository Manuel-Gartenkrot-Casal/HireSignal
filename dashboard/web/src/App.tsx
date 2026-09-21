import { useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ShimmeringText } from "@/components/shimmering-text";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  ChartTooltip,
  Grid,
  PieCenter,
  PieChart,
  PieSlice,
} from "@/components/charts";
import { cn } from "@/lib/utils";
import { fetchJobs, fetchStats, type Bucket, type Job, type Stats } from "@/lib/api";

type SeniorityColor = Record<string, string>;

const seniorityColor: SeniorityColor = {
  junior: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  mid: "bg-sky-500/15 text-sky-600 dark:text-sky-400",
  senior: "bg-violet-500/15 text-violet-600 dark:text-violet-400",
  lead: "bg-amber-500/20 text-amber-600 dark:text-amber-400",
  unknown: "bg-muted text-muted-foreground",
};

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "short" });
}

function StatCard({
  label,
  value,
  sub,
  index,
}: {
  label: string;
  value: number;
  sub?: string;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card className="p-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">
          {value.toLocaleString()}
        </p>
        {sub ? (
          <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
        ) : null}
      </Card>
    </motion.div>
  );
}

type TooltipPoint = { point: Record<string, unknown> };

function AreaChartCard({ data }: { data: { _id: string; n: number }[] }) {
  const series = useMemo(
    () =>
      data.map((d) => ({
        date: new Date(`${d._id}T00:00:00`),
        jobs: d.n,
      })),
    [data]
  );

  if (!series.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Vacantes por día</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Sin datos.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Vacantes por día</CardTitle>
      </CardHeader>
      <CardContent>
        <AreaChart
          data={series as unknown as Record<string, unknown>[]}
          aspectRatio="2 / 1"
          className="h-64"
        >
          <Grid strokeDasharray="3,3" />
          <Area
            dataKey="jobs"
            fill="var(--chart-line-primary)"
            fillOpacity={0.25}
            showHighlight
          />
          <ChartTooltip
            content={({ point }: TooltipPoint) => (
              <div className="rounded-lg border bg-background px-3 py-1.5 text-xs shadow-md">
                <span className="font-medium">
                  {new Date(point.date as string).toLocaleDateString("es-AR", {
                    day: "2-digit",
                    month: "short",
                  })}
                </span>
                <span className="ml-2 font-mono">{point.jobs as number}</span>
              </div>
            )}
          />
        </AreaChart>
      </CardContent>
    </Card>
  );
}

function BarChartCard({ data }: { data: Bucket[] }) {
  const series = useMemo(
    () =>
      data.map((d, i) => ({
        name: d._id,
        count: d.n,
        color: CHART_COLORS[i % CHART_COLORS.length],
      })),
    [data]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Por seniority</CardTitle>
      </CardHeader>
      <CardContent>
        {series.length ? (
          <BarChart
            data={series as unknown as Record<string, unknown>[]}
            xDataKey="name"
            aspectRatio="2 / 1"
            className="h-64"
          >
            <Grid strokeDasharray="3,3" />
            <Bar dataKey="count" />
            <ChartTooltip
              content={({ point }: TooltipPoint) => (
                <div className="rounded-lg border bg-background px-3 py-1.5 text-xs shadow-md">
                  <span className="font-medium capitalize">
                    {point.name as string}
                  </span>
                  <span className="ml-2 font-mono">{point.count as number}</span>
                </div>
              )}
            />
          </BarChart>
        ) : (
          <p className="text-sm text-muted-foreground">Sin datos.</p>
        )}
      </CardContent>
    </Card>
  );
}

function PieChartCard({ data }: { data: Bucket[] }) {
  const pies = useMemo(
    () =>
      data.map((d, i) => ({
        label: d._id,
        value: d.n,
        color: CHART_COLORS[i % CHART_COLORS.length],
      })),
    [data]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Por fuente</CardTitle>
      </CardHeader>
      <CardContent>
        {pies.length ? (
          <div className="flex flex-col items-center gap-4 sm:flex-row">
            <PieChart
              className="w-52 shrink-0"
              data={pies}
              innerRadius={55}
              padAngle={0.02}
              cornerRadius={4}
            >
              {pies.map((p, i) => (
                <PieSlice hoverEffect="translate" index={i} key={p.label} />
              ))}
              <PieCenter defaultLabel="total" />
            </PieChart>
            <div className="flex w-full flex-col gap-1.5 text-sm">
              {pies.map((p) => (
                <div
                  className="flex items-center justify-between gap-2"
                  key={p.label}
                >
                  <span className="flex items-center gap-2 capitalize">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: p.color }}
                    />
                    {p.label}
                  </span>
                  <span className="font-mono tabular-nums">
                    {p.value.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Sin datos.</p>
        )}
      </CardContent>
    </Card>
  );
}

function JobsTable({ jobs, loading }: { jobs: Job[]; loading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Vacantes activas</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Cargo</TableHead>
              <TableHead>Empresa</TableHead>
              <TableHead className="hidden md:table-cell">Seniority</TableHead>
              <TableHead className="hidden sm:table-cell">Fecha</TableHead>
              <TableHead className="text-right">Fuente</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading
              ? Array.from({ length: 8 }, (_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={5}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              : jobs.map((j) => (
                  <TableRow key={j._id}>
                    <TableCell className="max-w-[280px]">
                      <a
                        className="line-clamp-1 font-medium hover:text-primary"
                        href={j.url}
                        rel="noreferrer"
                        target="_blank"
                        title={j.title}
                      >
                        {j.title}
                      </a>
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      {j.company}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      <Badge
                        className={cn(
                          "capitalize",
                          seniorityColor[j.seniority] ??
                            seniorityColor.unknown
                        )}
                        variant="outline"
                      >
                        {j.seniority}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden text-muted-foreground sm:table-cell">
                      {formatDate(j.posted_date)}
                    </TableCell>
                    <TableCell className="text-right capitalize text-muted-foreground">
                      {j.source}
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function App() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [seniority, setSeniority] = useState("all");
  const [role, setRole] = useState("all");

  useEffect(() => {
    fetchStats().catch(() => null).then(setStats);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchJobs({ q: q || undefined, seniority, role })
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, [q, seniority, role]);

  const seniorityOptions = useMemo(
    () => [
      { value: "all", label: "Todas" },
      ...(stats?.porSeniority ?? [])
        .map((b) => ({ value: b._id, label: b._id }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    ],
    [stats]
  );

  const roleOptions = useMemo(
    () => [
      { value: "all", label: "Todos" },
      ...(stats?.porRol ?? []).map((b) => ({
        value: b._id,
        label: b._id,
      })),
    ],
    [stats]
  );

  const totalSenior = useMemo(
    () =>
      (stats?.porSeniority ?? []).reduce(
        (acc, b) => acc + (b._id === "senior" || b._id === "lead" ? b.n : 0),
        0
      ),
    [stats]
  );

  const ultimaSemana = useMemo(
    () =>
      (stats?.recientes ?? [])
        .slice(-7)
        .reduce((acc, d) => acc + d.n, 0),
    [stats]
  );

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <ShimmeringText
              className="text-2xl font-bold tracking-tight"
              text="HireSignal"
            />
            <Badge variant="secondary">MVP</Badge>
          </div>
          <p className="hidden text-sm text-muted-foreground sm:block">
            Feed de vacantes · {new Date().toLocaleDateString("es-AR")}
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-6 py-6">
        <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard
            index={0}
            label="Vacantes activas"
            sub="en el pipeline"
            value={stats?.total ?? 0}
          />
          <StatCard
            index={1}
            label="Senior / Lead"
            sub="perfil avanzado"
            value={totalSenior}
          />
          <StatCard
            index={2}
            label="Últimos 7 días"
            sub="publicadas"
            value={ultimaSemana}
          />
          <StatCard
            index={3}
            label="Fuentes"
            sub={(stats?.porFuente ?? []).length + " ATS"}
            value={(stats?.porFuente ?? []).length}
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <AreaChartCard data={stats?.recientes ?? []} />
          <BarChartCard data={stats?.porSeniority ?? []} />
        </section>

        <PieChartCard data={stats?.porFuente ?? []} />

        <Card>
          <CardHeader>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-sm">Explorar vacantes</CardTitle>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Input
                  className="w-full sm:w-64"
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Buscar cargo…"
                  type="search"
                  value={q}
                />
                <select
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  onChange={(e) => setSeniority(e.target.value)}
                  value={seniority}
                >
                  {seniorityOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      Seniority: {o.label}
                    </option>
                  ))}
                </select>
                <select
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  onChange={(e) => setRole(e.target.value)}
                  value={role}
                >
                  {roleOptions.map((o) => (
                    <option key={o.value} value={o.value}>
                      Rol: {o.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardHeader>
        </Card>

        <JobsTable jobs={jobs} loading={loading} />
      </main>

      <footer className="border-t py-4 text-center text-xs text-muted-foreground">
        HireSignal · scraping pipeline + MongoDB + dashboard
      </footer>
    </div>
  );
}