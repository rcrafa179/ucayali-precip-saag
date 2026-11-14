"""Sube al repositorio los resultados de UN año, siempre de la misma forma.

Uso (desde la carpeta del repo, después de extraer y de hacer los mapas de ese año):
    python scripts/06_subir_anio.py 2010

Comprueba que exista data/processed/saag_pr_diaria_FMA_<año>.nc y que esté completo (89 días,
sin horas faltantes), y sube SOLO:
    data/processed/saag_pr_diaria_FMA_<año>.nc
    figures/mapas_total_<año>.png, figures/mapas_diaslluvia_<año>.png, figures/mapas_resumen_mensual_<año>.csv
Si faltan las figuras, las genera antes con 04_mapas_mensuales.py.
"""
import subprocess, sys
import xarray as xr
from config import PROCESSED, FIGURAS, RAIZ, PERIODO, dias


def git(*a, ok=False):
    print("$ git " + " ".join(a))
    r = subprocess.run(["git", *a], cwd=RAIZ)
    if r.returncode and not ok:
        sys.exit(f"git {a[0]} falló; revisa el mensaje de arriba.")
    return r.returncode


if len(sys.argv) != 2:
    sys.exit(__doc__)
anio = int(sys.argv[1])
nc = PROCESSED / f"saag_pr_diaria_{PERIODO}_{anio}.nc"
if not nc.exists():
    sys.exit(f"No existe {nc.relative_to(RAIZ)}. Primero: python scripts/01_extraer_saag.py {anio} --workers 20")
d = xr.open_dataset(nc)
n, inc = d.sizes["time"], int((d.n_horas < 24).sum())
d.close()
if n != len(dias(anio)) or inc:
    sys.exit(f"{nc.name}: {n} días, {inc} incompletos. Completa la extracción antes de subirlo.")
print(f"{nc.name}: {n} días, completo")

figs = [FIGURAS / f"mapas_total_{anio}.png", FIGURAS / f"mapas_diaslluvia_{anio}.png",
        FIGURAS / f"mapas_resumen_mensual_{anio}.csv"]
if not all(f.exists() for f in figs):
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "04_mapas_mensuales.py"), str(anio)], cwd=RAIZ, check=True)

archivos = [str(p.relative_to(RAIZ)) for p in [nc, *figs]]
git("add", "--", *archivos)
if git("diff", "--cached", "--quiet", ok=True) == 0:
    sys.exit("No hay cambios que subir: esos archivos ya están en el repositorio.")
git("commit", "-m", f"SAAG: resultados FMA {anio}", "--", *archivos)
git("pull", "--rebase")
git("push")
print(f"\nListo: resultados de {anio} subidos.")
