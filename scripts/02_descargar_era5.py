"""
Descarga ERA5 precipitación total HORARIA para la caja del Ucayali, solo FMA
(+ el 1 de mayo, necesario para cerrar el último día pluviométrico de abril).
El paso a diario se hace en 03_diario_obs.py con la misma definición de día que el SAAG.

Requiere cuenta en Copernicus CDS, haber aceptado la licencia de
"ERA5 hourly data on single levels" y el token en ~/.cdsapirc.

Uso (desde la raíz del repo): python scripts/02_descargar_era5.py 2005 2010 2015
"""
import sys
import cdsapi
from config import AREA_CDS, RAW_ERA5, ANIOS, MESES

RAW_ERA5.mkdir(parents=True, exist_ok=True)
c = cdsapi.Client()

for anio in [int(a) for a in sys.argv[1:]] or ANIOS:
    pedidos = [(m, list(range(1, 32))) for m in MESES] + [(MESES[-1] + 1, [1])]
    for mes, dias in pedidos:
        f = RAW_ERA5 / f"era5_tp_{anio}{mes:02d}.nc"
        if f.exists():
            continue
        c.retrieve("reanalysis-era5-single-levels", {
            "product_type": ["reanalysis"],
            "variable": ["total_precipitation"],
            "year": [str(anio)],
            "month": [f"{mes:02d}"],
            "day": [f"{d:02d}" for d in dias],
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": AREA_CDS,
            "data_format": "netcdf",
        }, str(f))
        print("ok", f)
# tp está en metros (x1000 -> mm). El valor a la hora H es lo acumulado entre H-1 y H (UTC),
# misma convención que PREC_ACC_NC del SAAG.
