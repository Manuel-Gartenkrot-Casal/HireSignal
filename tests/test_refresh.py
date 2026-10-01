from hire_signal.db import _debe_cerrar


def test_guarda_contra_cierre_masivo():
    assert _debe_cerrar(100, 10)       # recambio normal
    assert not _debe_cerrar(100, 80)   # respuesta incompleta: no cerrar
    assert _debe_cerrar(0, 0)          # nada activo previo
