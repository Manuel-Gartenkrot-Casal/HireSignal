import {
  Link000,
  Link001,
  Link002,
  Link003,
  Link004,
  Link005,
} from "@/components/ui/skiper-ui/skiper40"

const REPO = "https://github.com/Manuel-Gartenkrot-Casal/HireSignal"

const fuentes = [
  { name: "Greenhouse", href: "https://www.greenhouse.com" },
  { name: "Lever", href: "https://www.lever.co" },
  { name: "Ashby", href: "https://www.ashbyhq.com" },
  { name: "GetOnBrd", href: "https://www.getonbrd.com" },
]

export default function Page() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex items-center justify-between p-6">
        <Link000 href="/" className="font-medium">
          HireSignal
        </Link000>
        <Link001 href={REPO} className="text-sm">
          GitHub
        </Link001>
      </header>

      <main className="flex flex-1 flex-col items-start justify-center gap-10 px-6">
        <div className="flex max-w-xl flex-col gap-3">
          <h1 className="text-4xl font-medium tracking-tight">
            Tu próximo cliente ya está contratando
          </h1>
          <p className="text-muted-foreground">
            Para software factories y agencias de staffing IT: cada lunes, las
            empresas tech que más vacantes de backend, data o DevOps abrieron
            esa semana, con el link a cada búsqueda y listas para tu CRM.
            USD 49/mes · 14 días gratis.
          </p>
        </div>

        <div className="flex flex-wrap gap-6 text-lg">
          <Link004 href={`${REPO}#readme`}>Documentación</Link004>
          <Link005 href={`${REPO}/issues`}>Reportar un problema</Link005>
        </div>

        <div className="flex flex-col gap-2">
          <span className="text-xs text-muted-foreground uppercase">Fuentes</span>
          <ul className="flex flex-wrap gap-x-6 gap-y-2">
            {fuentes.map((f) => (
              <li key={f.name}>
                <Link002 href={f.href}>{f.name}</Link002>
              </li>
            ))}
          </ul>
        </div>
      </main>

      <footer className="flex p-6 text-xs text-muted-foreground">
        <Link003 href="https://skiper-ui.com">Links animados por Skiper UI</Link003>
      </footer>
    </div>
  )
}
