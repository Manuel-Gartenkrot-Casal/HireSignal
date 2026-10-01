import re

ROLES = {
    "backend": [
        "backend", "back-end", "back end", "api", "node", "python", "java", "golang", "go ",
        "ruby", "php", ".net", "elixir", "scala", "spring", "django", "fastapi", "microservice",
        "desarrollador back", "desarrollador de software", "rust", "system administrator",
        "administrador de sistemas",
    ],
    "frontend": [
        "frontend", "front-end", "front end", "react", "vue", "angular", "typescript",
        "javascript", "css", "html", "next.js", "web", "front",
    ],
    "fullstack": ["fullstack", "full-stack", "full stack"],
    "data": [
        "data", "analytics", "analista", "sql", "etl", "big data", "machine learning", "ml ",
        "ai ", "artificial intelligence", "dato", "científico de datos", "cientista",
        "data science", "inteligencia artificial", "business intelligence", "bi",
    ],
    "devops": [
        "devops", "sre", "site reliability", "cloud", "aws", "azure", "gcp", "kubernetes",
        "docker", "ci/cd", "infra", "infrastructure", "platform engineer",
        "infraestructura", "consultor cloud",
    ],
    "qa": ["qa", "quality", "tester", "testing", "test automation", "control de calidad"],
    "mobile": [
        "mobile", "ios", "android", "flutter", "react native", "kotlin", "swift",
        "desarrollador móvil",
    ],
    "security": ["security", "seguridad", "cyber", "pentest", "soc", "appsec", "hacking"],
    "product": [
        "product manager", "product designer", "pm ", "producto", "product owner",
        "gestión de producto",
    ],
    "engineering": [
        "engineering manager", "engineering lead", "eng manager", "director de ingeniería",
        "head of engineering", "vp of engineering", "director de tecnología", "cto",
    ],
    "design": [
        "designer", "design", "ux", "ui", "figma", "diseñador", "diseño", "product designer",
    ],
    "hr": [
        "hr ", "people", "talent", "recruiter", "recruitment", "recursos humanos",
        "talent acquisition",
    ],
    "sales": [
        "sales", "ventas", "bdr", "account executive", "comercial", "sdr", "business development",
        "account manager", "client partner", "partnerships", "vendas", "vendedor",
    ],
    "marketing": [
        "marketing", "growth", "seo", "content", "comunicación", "copywriter", "comunicaciones",
        "brand", "branding",
    ],
    "finance": [
        "finance", "finanzas", "accountant", "controller", "contador", "financial", "monetización",
        "treasury", "tax", "credit", "underwriter", "risk", "riesgo", "fraud", "fraude", "accounting",
    ],
    "support": ["support", "soporte", "customer success", "desk", "atención al cliente", "customer service", "atendimento"],
    "operations": [
        "operations", "operaciones", "operações", "logística", "logistics", "supply chain", "procurement",
        "supervisor", "supervisión", "supervisão", "mantenimiento", "manutenção", "transporte",
        "warehouse", "almacén", "última milla", "last mile",
    ],
    "legal": [
        "legal", "counsel", "compliance", "attorney", "paralegal", "abogado", "jurídico", "privacy", "regulatory",
    ],
    "leadership": [
        "head", "lead ", "leader", "director", "vp ", "c-level", "cto", "coo", "ceo",
        "chief", "founder", "co-founder", "gerente",
    ],
}

# Palabras de ingeniería genérica: SOLO como fallback si ninguna categoría
# específica matcheó (evita que "Frontend Engineer" caiga en backend).
GENERIC_ENG = [
    "engineer", "developer", "software", "programador", "desarrollador", "ingeniero",
    "sistemas", "desarrollo", "arquitecto",
]

SENIORITY = {
    "junior": [
        "junior", "jr", "jr.", "entry", "trainee", "pasantía", "pasantias", "intern",
        "júnior", "asistente", "assistant", "practicante", "prácticas", "becario",
        " i ", " grado i", "nivel i", "júnior.",
    ],
    "mid": [
        "mid", "semisenior", "semi senior", "semi-senior", "intermediate", "pleno", "ssr",
        " ii ", "nivel ii", "grado ii",
    ],
    "senior": [
        "senior", "sr", "sr.", "sênior", "advanced", "staff", "expert", "sénior",
        " iii ", "nivel iii", "grado iii",
    ],
    "lead": [
        "lead", "head", "principal", "tech lead", "líder", "lider", "lead ", "director",
        "gerente", "gerencia", "gerência", "jefe", "coordinador", "coordenador",
    ],
}

TECH_STACK = [
    "python", "javascript", "typescript", "java", "golang", "go", "ruby", "php",
    "node", "node.js", "react", "vue", "angular", "next.js", "nest", "django",
    "flask", "fastapi", "spring", "express", "graphql", "rest", "sql", "postgres",
    "postgresql", "mysql", "mongodb", "redis", "kafka", "aws", "azure", "gcp",
    "docker", "kubernetes", "k8s", "terraform", "airflow", "spark", "hadoop",
    "pandas", "numpy", "scikit", "tensorflow", "pytorch", "llm", "ml", "nlp",
    "flutter", "kotlin", "swift", "react native", "c#", ".net", "c++", "rust",
    "elixir", "scala", "clojure", "perl", "shell", "bash", "linux", "git",
    "jenkins", "github actions", "circleci", "databricks", "snowflake",
    "dbt", "tableau", "power bi", "looker", "salesforce", "zendesk",
]

# Reglas de seniority por años de experiencia (fallback por descripción).
# Claves: experiencia mínima. "none" = sin exigencia = junior.
YRS_SENIORITY = [
    (8, "lead"),
    (6, "senior"),
    (4, "senior"),
    (3, "mid"),
    (2, "mid"),
    (1, "junior"),
    (0, "junior"),
]


def _normalizar(texto: str) -> str:
    return f" {texto.lower()} "


def _kw(termino: str) -> str:
    """Padea con espacios los keywords cortos para no matchear dentro de
    otras palabras (ej. 'ui' no debe matchear 'acquisition', 'soc' no debe
    matchear 'associate')."""
    if len(termino.strip()) <= 4 and termino != ".net":
        return f" {termino.strip()} "
    return termino


def _match(texto: str, kws: list[str]) -> bool:
    return any(_kw(kws_str) in texto for kws_str in kws)


def _extract_years(texto: str) -> int | None:
    """Busca patrones tipo '5+ years', '5-7 years', '3+ años'."""
    patterns = [
        r"(\d{1,2})\s*\+\s*(?:years|años|anos)",
        r"(\d{1,2})\s*[-–]\s*\d{1,2}\s*(?:years|años|anos)",
        r"(?:years|años|anos)\s+of\s+experience\s+(\d{1,2})",
        r"(?:minimum of|at least)\s+(\d{1,2})\s*(?:\+|plus)?\s*(?:years|años|anos)",
        r"(\d{1,2})\s*(?:\+|plus)\s*years?",
    ]
    for pat in patterns:
        m = re.search(pat, texto)
        if m:
            yr = int(m.group(1))
            # YRS_SENIORITY está ordenado desc: el primero cuyo mínimo se
            # cumple manda.
            for min_y, lvl in YRS_SENIORITY:
                if yr >= min_y:
                    return lvl
    return None


def clasificar(title: str, description: str = "") -> dict:
    """Clasificación por TÍTULO (regla del plan). La descripción SOLO se usa
    como apoyo conservador: para inferir seniority cuando el título no lo dice
    (años de experiencia) y para detectar tecnologías. El rol siempre nace del
    título, porque las descripciones mezclan keywords de otros equipos y
    generan ruido.
    """
    texto = _normalizar(title)
    roles = [r for r, kws in ROLES.items() if _match(texto, kws)]
    es_eng = any(_kw(g) in texto for g in GENERIC_ENG)
    # "Payments Compliance Engineer" es ingeniería, no legal/operaciones.
    roles = [r for r in roles if not (es_eng and r in ("legal", "operations"))]

    # Seniority sobre el título sin puntuación: "Manager II, Search" debe ver " ii ".
    sen = _normalizar(re.sub(r"[^\w]+", " ", title)).replace(" mid market ", " ")
    seniority = "unknown"
    for nivel, kws in SENIORITY.items():
        if _match(sen, kws):
            seniority = nivel
            break

    tech = sorted({t for t in TECH_STACK if _kw(t) in texto})

    # Apoyo con descripción (solo seniority por años y tech).
    if description:
        desc = _normalizar(description)
        if seniority == "unknown":
            by_year = _extract_years(desc)
            if by_year:
                seniority = by_year
        tech = sorted(set(tech) | {t for t in TECH_STACK if _kw(t) in desc})

    # Último recurso: ingeniería genérica (solo si nada matcheó, para no
    # pisar categorías específicas).
    if not roles:
        if es_eng:
            roles = ["backend"]
        else:
            roles = ["other"]

    return {
        "role_category": roles[0] if roles else "other",
        "seniority": seniority,
        "tech": ", ".join(tech) if tech else "",
    }


def aplicar_a_job(job) -> None:
    """Rellena role_category/seniority/tech según el título (y descripción) del job.

    Respeta valores ya cargados por la fuente (p. ej. getonbrd trae seniority
    oficial): solo clasifica donde el campo esté vacío.
    """
    res = clasificar(job.title, getattr(job, "description", "") or "")
    if not getattr(job, "role_category", ""):
        job.role_category = res["role_category"]
    if not getattr(job, "seniority", ""):
        job.seniority = res["seniority"]
    if not getattr(job, "tech", ""):
        job.tech = res["tech"]