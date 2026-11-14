"""Descarga ERA5 precipitación total HORARIA para la cuenca, solo FMA de los años del proyecto
(+ el 1 de mayo, necesario para cerrar el último día pluviométrico de abril).
El paso a diario se hace en 03_diario_obs.py con la misma definición de día que el SAAG.

Primera vez (guarda tu clave en ~/.cdsapirc, fuera del repo; no hay que repetirlo):
    python scripts/02_descargar_era5.py --clave TU-TOKEN-DE-CDS

Descargar (sin años = 2005, 2010 y 2015):
    python scripts/02_descargar_era5.py
    python scripts/02_descargar_era5.py 2010

Antes, una sola vez en la web:
  1. Crear cuenta en https://cds.climate.copernicus.eu
  2. Copiar el "Personal Access Token" de tu perfil (https://cds.climate.copernicus.eu/profile)
  3. Aceptar la licencia en la pestaña "Download" de "ERA5 hourly data on single levels"
     (https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), al final de la página.

Son 4 pedidos por año (feb, mar, abr, 1-may), unos pocos MB en total. Cada pedido espera en la cola
de Copernicus (de segundos a varios minutos). Los archivos ya descargados se saltan.
"""
import os
import sys
from pathlib import Path

from config import RAW_ERA5, ANIOS, MESES, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

URL_CDS = "https://cds.climate.copernicus.eu/api"
RC = Path.home() / ".cdsapirc"
# Área alineada a la malla de 0.25° de ERA5 (si no, el CDS interpola) e incluyendo toda celda cuyo
# cuadrado de 0.25° toque la caja del dominio (centros hasta medio paso por fuera).
import math
AREA = [math.ceil((LAT_MAX + 0.125) * 4) / 4, math.floor((LON_MIN - 0.125) * 4) / 4,
        math.floor((LAT_MIN - 0.125) * 4) / 4, math.ceil((LON_MAX + 0.125) * 4) / 4]   # N, O, S, E


def guardar_clave(clave):
    clave = clave.strip()
    if ":" in clave:   # formato antiguo UID:KEY -> el CDS nuevo solo usa el token
        print("Aviso: el CDS nuevo usa solo el token (sin 'UID:'). Se guarda tal cual; si falla, copia el token de tu perfil.")
    RC.write_text(f"url: {URL_CDS}\nkey: {clave}\n")
    os.chmod(RC, 0o600)
    print(f"Clave guardada en {RC} (solo en tu computadora, no en el repo).")


def cliente():
    try:
        import cdsapi
    except ImportError:
        sys.exit('Falta cdsapi: pip install "cdsapi>=0.7.4"')
    if not RC.exists() and not os.environ.get("CDSAPI_KEY"):
        sys.exit("No hay clave de Copernicus. Primero: python scripts/02_descargar_era5.py --clave TU-TOKEN")
    return cdsapi.Client()


def descargar(c, anio):
    RAW_ERA5.mkdir(parents=True, exist_ok=True)
    pedidos = [(m, list(range(1, 32))) for m in MESES] + [(MESES[-1] + 1, [1])]
    for mes, dias in pedidos:
        f = RAW_ERA5 / f"era5_tp_{anio}{mes:02d}.nc"
        if f.exists() and f.stat().st_size > 0:
            print(f"{f.name} ya existe, salto")
            continue
        print(f"Pidiendo ERA5 {anio}-{mes:02d} ...", flush=True)
        c.retrieve("reanalysis-era5-single-levels", {
            "product_type": ["reanalysis"],
            "variable": ["total_precipitation"],
            "year": [str(anio)],
            "month": [f"{mes:02d}"],
            "day": [f"{d:02d}" for d in dias],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": AREA,
            "data_format": "netcdf",
            "download_format": "unarchived",
        }, str(f))
        print(f"  ok {f.name}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--clave" in args:
        i = args.index("--clave")
        if i + 1 >= len(args):
            sys.exit("Falta el token después de --clave")
        guardar_clave(args[i + 1]); del args[i:i + 2]
        if not args:
            print("Ahora: python scripts/02_descargar_era5.py   (descarga 2005, 2010 y 2015)")
            sys.exit(0)
    c = cliente()
    for anio in [int(a) for a in args] or ANIOS:
        descargar(c, anio)
    print("\nSiguiente: python scripts/03_diario_obs.py era5   y luego   python scripts/08_comparar.py era5")
# tp está en metros (x1000 -> mm). El valor a la hora H es lo acumulado entre H-1 y H (UTC),
# misma convención que PREC_ACC_NC del SAAG.
