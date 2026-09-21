import re

ROLES = {
    "backend": ["backend", "back-end", "back end", "api", "node", "python", "java", "golang", "go ", "ruby", "php", ".net", "elixir", "scala", "spring"],
    "frontend": ["frontend", "front-end", "front end", "react", "vue", "angular", "typescript", "javascript", "css", "html", "next.js", "ux/ui", "ui designer", "web"],
    "fullstack": ["fullstack", "full-stack", "full stack"],
    "data": ["data", "analytics", "analista", "sql", "etl", "big data", "machine learning", "ml ", "ai ", "artificial intelligence", "dato"],
    "devops": ["devops", "sre", "site reliability", "cloud", "aws", "azure", "gcp", "kubernetes", "docker", "ci/cd", "infra"],
    "qa": ["qa", "quality", "tester", "testing", "test automation"],
    "mobile": ["mobile", "ios", "android", "flutter", "react native", "kotlin", "swift"],
    "security": ["security", "seguridad", "cyber", "pentest", "soc", "appsec"],
    "product": ["product manager", "product designer", "pm ", "producto"],
    "engineering": ["engineering manager", "engineering lead", "eng manager"],
    "design": ["designer", "design", "ux", "ui", "figma"],
    "hr": ["hr ", "people", "talent", "recruiter", "recruitment", "recursos humanos"],
    "sales": ["sales", "ventas", "bdr", "account executive", "comercial"],
    "marketing": ["marketing", "growth", "seo", "content", "comunicación", "copywriter"],
    "finance": ["finance", "finanzas", "accountant", "controller", "contador", "financial"],
    "support": ["support", "soporte", "customer", "success", "desk"],
    "leadership": ["head", "lead ", "leader", "director", "vp ", "c-level", "cto", "coo", "ceo"],
}

SENIORITY = {
    "junior": ["junior", "jr", "jr.", "entry", "trainee", "pasantía", "intern"],
    "mid": ["mid", "semisenior", "semi senior", "semi-senior", "intermediate"],
    "senior": ["senior", "sr", "sr.", "advanced", "staff", "expert"],
    "lead": ["lead", "head", "principal"],
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


def _normalizar(texto: str) -> str:
    return f" {texto.lower()} "


def _kw(termino: str) -> str:
    """Padea con espacios los keywords cortos para no matchear dentro de
    otras palabras (ej. 'ui' no debe matchear 'acquisition', 'soc' no debe
    matchear 'associate')."""
    if len(termino.strip()) <= 4 and termino != ".net":
        return f" {termino.strip()} "
    return termino


def clasificar(title: str, description: str = "") -> dict:
    # Clasificación por TÍTULO (regla del plan: keyword matching en título).
    # La descripción se ignora por defecto: contiene keywords de todos los
    # roles/tech y genera ruido.
    texto = _normalizar(title)
    roles = [r for r, kws in ROLES.items() if any(_kw(kw) in texto for kw in kws)]
    seniority = "unknown"
    for nivel, kws in SENIORITY.items():
        if any(_kw(kw) in texto for kw in kws):
            seniority = nivel
            break
    tech = sorted({t for t in TECH_STACK if _kw(t) in texto})
    return {
        "role_category": roles[0] if roles else "other",
        "seniority": seniority,
        "tech": ", ".join(tech) if tech else "",
    }


def aplicar_a_job(job) -> None:
    """Rellena role_category/seniority/tech según el título del job."""
    res = clasificar(job.title)
    job.role_category = res["role_category"]
    job.seniority = res["seniority"]
    job.tech = res["tech"]