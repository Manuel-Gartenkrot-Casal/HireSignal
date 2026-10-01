import datetime

from hire_signal.models import Job
from hire_signal.spiders.base import _coerce_fecha


def test_dedup_key_ignora_formato_de_empresa_y_titulo():
    a = Job("Acme Inc", "Senior Backend Engineer (Remote)", "u1", "greenhouse")
    b = Job("ACME", "senior  backend engineer", "u2", "ashby")
    assert a.dedup_key == b.dedup_key


def test_dedup_key_distingue_puestos():
    a = Job("Acme", "Backend Engineer", "u", "greenhouse")
    b = Job("Acme", "Frontend Engineer", "u", "greenhouse")
    assert a.dedup_key != b.dedup_key


def test_coerce_fecha():
    iso = _coerce_fecha("2026-01-05T10:00:00Z")
    assert iso == datetime.datetime(2026, 1, 5, 10, tzinfo=datetime.UTC)
    assert _coerce_fecha(1767607200000) == _coerce_fecha(1767607200)  # ms == s
    assert _coerce_fecha("no es fecha") is None
    assert _coerce_fecha(None) is None


def test_dedupe_fusiona_ubicaciones():
    from hire_signal.pipeline import _dedupe

    jobs = [Job("Acme", "Backend Engineer", "u", "greenhouse", location=c) for c in ("Austin", "London", "Austin")]
    jobs.append(Job("Acme", "Data Analyst", "u", "greenhouse", location="Paris"))
    out = _dedupe(jobs)
    assert len(out) == 2
    assert out[0].location == "Austin; London"
    assert _dedupe([Job("A", "T", "u", "g", location=str(i)) for i in range(7)])[0].location.endswith("(+2)")
