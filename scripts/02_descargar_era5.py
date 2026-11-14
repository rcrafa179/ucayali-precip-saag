"""
Descarga ERA5 precipitación total horaria para la caja del Ucayali.
Requiere cuenta en Copernicus CDS, haber aceptado la licencia de
"ERA5 hourly data on single levels" y el token en ~/.cdsapirc.

Uso (desde la raíz del repo): python scripts/02_descargar_era5.py 2005 2010 2015
"""
import sys
import cdsapi
from config import AREA_CDS as AREA, RAW_ERA5 as SALIDA, ANIOS

SALIDA.mkdir(parents=True, exist_ok=True)
c = cdsapi.Client()

for anio in sys.argv[1:] or ANIOS:
    for mes in range(1, 13):
        f = SALIDA / f"era5_tp_{anio}{mes:02d}.nc"
        if f.exists():
            continue
        c.retrieve("reanalysis-era5-single-levels", {
            "product_type": ["reanalysis"],
            "variable": ["total_precipitation"],
            "year": [str(anio)],
            "month": [f"{mes:02d}"],
            "day": [f"{d:02d}" for d in range(1, 32)],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": AREA,
            "data_format": "netcdf",
        }, str(f))
        print("ok", f)
# Nota: tp está en metros (x1000 -> mm) y el valor a la hora H es lo acumulado entre H-1 y H (UTC).
