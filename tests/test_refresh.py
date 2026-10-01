from hire_signal.db import _debe_cerrar


def test_guarda_contra_cierre_masivo():
    assert _debe_cerrar(100, 10)       # recambio normal
    assert not _debe_cerrar(100, 80)   # respuesta incompleta: no cerrar
    assert _debe_cerrar(0, 0)          # nada activo previo


def test_fuentes_vacias(monkeypatch):
    from hire_signal import scheduler
    from hire_signal.models import Job

    monkeypatch.setattr(scheduler, "_cargar_companies", lambda _: [{"ats": "greenhouse"}, {"ats": "meli"}])
    assert scheduler._fuentes_vacias([Job("a", "t", "u", "greenhouse")]) == ["meli sin jobs"]
    assert scheduler._fuentes_vacias([Job("a", "t", "u", "greenhouse"), Job("b", "t", "u", "meli")]) == []
