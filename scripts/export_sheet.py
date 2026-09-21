import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hire_signal.sheets import exportar


def main():
    n = exportar([])
    print(f"Sheet actualizado con {n} filas.")


if __name__ == "__main__":
    main()