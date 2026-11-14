"""
Pasa ERA5 (horario) e IMERG (30 min) a precipitación DIARIA del periodo FMA,
con la MISMA definición de día pluviométrico que el SAAG (config.DIA_INICIO_UTC).

Uso (desde la raíz del repo):
    python scripts/03_diario_obs.py era5  2005 2010 2015
    python scripts/03_diario_obs.py imerg 2005 2010 2015

Entradas:
    data/raw/era5/era5_tp_<YYYYMM>.nc              (02_descargar_era5.py)
    data/raw/imerg/<año>/*.nc4 (o *.nc)            (GES DISC, GPM_3IMERGHH V07, recortado)
Salidas:
    data/processed/era5_pr_diaria_FMA_<año>.nc
    data/processed/imerg_pr_diaria_FMA_<año>.nc
  Variables: pr [mm/día] y n_pasos (pasos válidos: ERA5 24, IMERG 48 = completo).
"""
import sys
import numpy as np
import pandas as pd
import xarray as xr
from config import (RAW_ERA5, RAW_IMERG, PROCESSED, ANIOS, PERIODO,
                    LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, DIA_INICIO_UTC, dias)


def a_diario(pr, fin_de_paso, anio, pasos_por_dia):
    """pr: DataArray (time, lat, lon) en mm por paso.
    fin_de_paso: True si la marca de tiempo es el FIN del intervalo (ERA5),
                 False si es el INICIO (IMERG)."""
    t = pd.DatetimeIndex(pr["time"].values)
    paso = (t[1] - t[0]) if len(t) > 1 else pd.Timedelta(hours=1)
    inicio = t - paso if fin_de_paso else t
    # día pluviométrico al que pertenece cada paso
    etiqueta = (inicio - pd.Timedelta(hours=DIA_INICIO_UTC)).floor("D")
    pr = pr.assign_coords(dia=("time", etiqueta))
    sel = pr["dia"].isin(dias(anio))
    pr = pr.where(sel, drop=True)
    total = pr.groupby("dia").sum("time", min_count=1)
    n = pr.notnull().all(dim=[d for d in pr.dims if d != "time"]).groupby("dia").sum()
    total = total.rename(dia="time")
    n = n.rename(dia="time")
    total = total.reindex(time=dias(anio))
    n = n.reindex(time=dias(anio), fill_value=0)
    ds = xr.Dataset({"pr": total.astype("float32"), "n_pasos": n.astype("int16")})
    ds["pr"].attrs = {"units": "mm/day", "long_name": "precipitación diaria acumulada"}
    ds["n_pasos"].attrs = {"long_name": f"pasos válidos en el día ({pasos_por_dia} = completo)"}
    ds.attrs["dia_pluviometrico"] = f"día D = [D {DIA_INICIO_UTC:02d} UTC, D+1 {DIA_INICIO_UTC:02d} UTC)"
    return ds


def era5(anio):
    archivos = sorted(RAW_ERA5.glob(f"era5_tp_{anio}*.nc"))
    if not archivos:
        sys.exit(f"No hay archivos ERA5 de {anio} en {RAW_ERA5}")
    ds = xr.open_mfdataset(archivos, combine="by_coords")
    if "valid_time" in ds.dims or "valid_time" in ds.coords:
        ds = ds.rename(valid_time="time")
    ds = ds.rename({k: v for k, v in {"latitude": "lat", "longitude": "lon"}.items() if k in ds.coords})
    tp = (ds["tp"] * 1000).sortby("time")          # m -> mm por hora
    tp = tp.drop_vars([v for v in tp.coords if v not in ("time", "lat", "lon")])
    out = a_diario(tp.load(), fin_de_paso=True, anio=anio, pasos_por_dia=24)
    out.attrs["fuente"] = "ERA5 total_precipitation horario"
    return out


def imerg(anio):
    carpeta = RAW_IMERG / str(anio)
    archivos = sorted(list(carpeta.glob("*.nc4")) + list(carpeta.glob("*.nc")))
    if not archivos:
        sys.exit(f"No hay archivos IMERG en {carpeta}")
    ds = xr.open_mfdataset(archivos, combine="by_coords")
    p = ds["precipitation"]                          # mm/hr, intervalos de 30 min
    p = p.transpose("time", "lat", "lon")
    p = p.sel(lat=slice(LAT_MIN, LAT_MAX), lon=slice(LON_MIN, LON_MAX))
    if hasattr(p.indexes["time"], "to_datetimeindex"):   # IMERG puede venir con calendario cftime
        p = p.assign_coords(time=p.indexes["time"].to_datetimeindex())
    p = p.sortby("time") * 0.5                       # mm/hr x 0.5 h = mm por paso
    out = a_diario(p.load(), fin_de_paso=False, anio=anio, pasos_por_dia=48)
    out.attrs["fuente"] = "GPM IMERG V07 Final, GPM_3IMERGHH"
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("era5", "imerg"):
        sys.exit(__doc__)
    fuente = sys.argv[1]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for anio in [int(a) for a in sys.argv[2:]] or ANIOS:
        ds = era5(anio) if fuente == "era5" else imerg(anio)
        f = PROCESSED / f"{fuente}_pr_diaria_{PERIODO}_{anio}.nc"
        ds.to_netcdf(f)
        inc = int((ds["n_pasos"] < (24 if fuente == "era5" else 48)).sum())
        print(f"{f.name}: {ds.sizes['time']} días, {inc} incompletos, "
              f"media de la caja {float(ds['pr'].mean()):.1f} mm/día")
