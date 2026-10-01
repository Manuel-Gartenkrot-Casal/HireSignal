"""Alta y baja de clientes pagos.

    python scripts/clave.py nueva cliente@agencia.com   -> imprime la clave
    python scripts/clave.py revocar cliente@agencia.com
    python scripts/clave.py listar

El cliente entra al dashboard con ?key=<clave> una vez; queda guardada en su navegador.
"""
import datetime
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hire_signal.db import db  # noqa: E402

claves = db["claves"]


def main(args: list[str]) -> int:
    if args[:1] == ["listar"]:
        for c in claves.find({}, {"_id": 0, "key": 0}):
            print(c)
        return 0
    if len(args) != 2 or args[0] not in ("nueva", "revocar"):
        print(__doc__)
        return 1
    accion, email = args[0], args[1].strip().lower()
    if accion == "revocar":
        n = claves.update_many({"email": email}, {"$set": {"activa": False}}).modified_count
        print(f"{n} clave(s) revocadas para {email}")
        return 0
    key = secrets.token_urlsafe(16)
    claves.insert_one({
        "key": key,
        "email": email,
        "activa": True,
        "creada": datetime.datetime.now(datetime.UTC).isoformat(),
    })
    claves.create_index("key", unique=True, name="uq_key")
    print(f"Clave para {email}: {key}\nLink: <URL del dashboard>/?key={key}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
