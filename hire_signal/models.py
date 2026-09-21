import dataclasses
import datetime
import hashlib
import re
from typing import Optional


@dataclasses.dataclass
class Job:
    company: str
    title: str
    url: str
    source: str
    ats: str = ""
    role_category: str = ""
    seniority: str = ""
    tech: str = ""
    location: str = ""
    posted_date: Optional[datetime.datetime] = None
    first_seen: datetime.datetime = dataclasses.field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    description: str = ""
    raw: dict = dataclasses.field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        """Clave de fusión entre fuentes: empresa + título normalizado.

        El mismo puesto publicado en Greenhouse y Lever debe colapsar en un
        solo documento con múltiples sources.
        """
        base = f"{normalizar_empresa(self.company)}|{normalizar_titulo(self.title)}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()


def normalizar_titulo(titulo: str) -> str:
    t = titulo.lower()
    t = re.sub(r"[\(\[].*?[\)\]]", " ", t)  # quita paréntesis/corchetes
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def normalizar_empresa(empresa: str) -> str:
    e = empresa.lower().strip()
    for sufijo in [" inc", " s.a.", " sa ", " llc", " ltd", " corp", " technologies", " srl"]:
        e = e.replace(sufijo, " ")
    e = re.sub(r"[^\w\s]", " ", e)
    e = re.sub(r"\s+", " ", e)
    return e.strip()