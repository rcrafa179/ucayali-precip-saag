"""
Precipitación DIARIA acumulada del WRF-SAAG (NCAR GDEX d616000) para la cuenca
del Ucayali, periodo FMA (feb-mar-abr) de 2005, 2010 y 2015.

El SAAG solo tiene salida horaria, así que el script lee las 24 horas de cada
día (solo PREC_ACC_NC y solo la caja, por OPeNDAP y en paralelo) y las suma.
La definición del día está en config.py (DIA_INICIO_UTC).

Uso (desde la raíz del repo):
    python scripts/01_extraer_saag.py prueba               # mide velocidad con un día
    python scripts/01_extraer_saag.py 2005                 # FMA 2005 (reanudable por mes)
    python scripts/01_extraer_saag.py 2005 --workers 8

Salida:
    data/raw/saag/<año>/saag_pr_diaria_<YYYYMM>.nc   (checkpoint mensual)
    data/processed/saag_pr_diaria_FMA_<año>.nc       (FMA completo, al terminar)
  Variables: pr [mm/día] y n_horas (horas válidas del día; 24 = completo).

Verificado con wrf2d_d01_2015-01-10_120000.nc:
  - PREC_ACC_NC [mm], PREC_ACC_DT = 60 min -> lluvia de la hora previa. CU_PHYSICS = 0.
  - Malla 1471 x 2027, fila 0 = sur. Dominio actual (5.3-4.4°S, 74.0-73.0°W) = y[1439:1467] x[292:322] (28 x 30).
  - Archivos: hist2D/<YYYYMM>/wrf2d_d01_<YYYY-MM-DD>_<HHMMSS>.nc
"""
import sys, time
from multiprocessing import Pool
import numpy as np
import pandas as pd
import xarray as xr
import netCDF4
from config import (LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, RAW_SAAG, PROCESSED,
                    MESES, PERIODO, DIA_INICIO_UTC, dias, horas_del_dia)

# ---------------- CONFIGURACIÓN ----------------
BASE = "https://tds.gdex.ucar.edu/thredds/dodsC/files/g/d616000"
URL_CONST = f"{BASE}/INVARIANT/wrfconstants_SAAG.nc"
RUTA_2D = "hist2D/{yyyymm}/wrf2d_d01_{fecha}_{hhmmss}.nc"
VAR = "PREC_ACC_NC"
SALIDA = RAW_SAAG
REINTENTOS = 4
WORKERS = 6   # peticiones simultáneas; no subir de ~12 para no saturar el servidor de NCAR
# ------------------------------------------------


def indices_caja():
    """Calcula (y0,y1,x0,x1) de la caja a partir de XLAT/XLONG y guarda la malla."""
    f = SALIDA / "malla_ucayali.nc"
    caja = f"{LAT_MIN},{LAT_MAX},{LON_MIN},{LON_MAX}"
    if f.exists():
        with xr.open_dataset(f) as m:
            if m.attrs.get("caja") == caja:
                return tuple(int(m.attrs[k]) for k in ("y0", "y1", "x0", "x1"))
        print("La caja de config.py cambió: se recalcula la malla.")
    print("Leyendo constantes del modelo...")
    c = xr.open_dataset(URL_CONST)
    lat = c["XLAT"].squeeze().values
    lon = c["XLONG"].squeeze().values
    dentro = (lat >= LAT_MIN) & (lat <= LAT_MAX) & (lon >= LON_MIN) & (lon <= LON_MAX)
    ys, xs = np.where(dentro)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    ydim, xdim = c["XLAT"].squeeze().dims
    sub = c[[v for v in ["XLAT", "XLONG", "HGT", "LANDMASK"] if v in c]].squeeze()
    sub = sub.isel({ydim: slice(y0, y1), xdim: slice(x0, x1)}).load()
    sub.attrs.update(y0=int(y0), y1=int(y1), x0=int(x0), x1=int(x1), caja=caja)
    SALIDA.mkdir(parents=True, exist_ok=True)
    sub.encoding.pop("unlimited_dims", None)
    sub.to_netcdf(f)
    print(f"Caja: y[{y0}:{y1}] x[{x0}:{x1}] -> {y1-y0} x {x1-x0} puntos. Malla guardada en {f}")
    return y0, y1, x0, x1


def url_hora(t):
    return f"{BASE}/" + RUTA_2D.format(
        yyyymm=t.strftime("%Y%m"), fecha=t.strftime("%Y-%m-%d"), hhmmss=t.strftime("%H%M%S"))


def url_recorte(t, caja):
    """URL OPeNDAP con restricción: solo VAR y solo la caja (índices inclusivos)."""
    y0, y1, x0, x1 = caja
    return f"{url_hora(t)}?{VAR}[0:1:0][{y0}:1:{y1-1}][{x0}:1:{x1-1}]"


def leer_hora(args):
    """Devuelve (t, array 2D float32) o (t, None) si falla tras los reintentos."""
    t, caja = args
    url = url_recorte(t, caja)
    for intento in range(REINTENTOS):
        try:
            with netCDF4.Dataset(url) as nc:
                a = nc.variables[VAR][0, :, :]
            return t, np.ma.filled(a.astype("float32"), np.nan)
        except Exception as e:
            espera = 10 * (intento + 1)
            print(f"  {t} intento {intento+1} falló ({e}); reintento en {espera}s", flush=True)
            time.sleep(espera)
    print(f"  !! {t} sin datos tras {REINTENTOS} intentos", flush=True)
    return t, None


def prueba(workers):
    caja = indices_caja()
    d = dias(2005)[0]
    horas = horas_del_dia(d)
    print(f"Día pluviométrico {d:%Y-%m-%d} = horas UTC {horas[0]:%m-%d %H}h ... {horas[-1]:%m-%d %H}h")
    print("URL ejemplo:", url_recorte(horas[0], caja))
    t0 = time.time()
    with Pool(workers) as p:
        res = p.map(leer_hora, [(h, caja) for h in horas])
    dt = time.time() - t0
    ok = [a for _, a in res if a is not None]
    if not ok:
        sys.exit("No se pudo leer ninguna hora. Revisa la URL de arriba.")
    total = np.sum(ok, axis=0)
    print(f"{len(ok)}/24 horas OK en {dt:.0f} s ({dt/24:.1f} s/h) | lluvia del día: "
          f"media {np.nanmean(total):.1f} mm, máx {np.nanmax(total):.1f} mm")
    n_h = len(dias(2005)) * 24
    print(f"-> FMA de un año ({n_h} h): ~{dt/24*n_h/3600:.1f} h")


def extraer_mes(anio, mes, caja, malla, workers):
    y0, y1, x0, x1 = caja
    f = SALIDA / str(anio) / f"saag_pr_diaria_{anio}{mes:02d}.nc"
    if f.exists():
        with xr.open_dataset(f) as viejo:
            igual = viejo.attrs.get("caja_indices") == f"y[{y0}:{y1}] x[{x0}:{x1}]"
        if igual:
            print(f"{f.name} ya existe, salto"); return f
        sys.exit(f"{f} es de otro dominio. Muévelo o bórralo y vuelve a correr.")
    f.parent.mkdir(parents=True, exist_ok=True)
    ds_mes = [d for d in dias(anio) if d.month == mes]
    tareas = [(h, caja) for d in ds_mes for h in horas_del_dia(d)]
    pos = {h: i for i, (h, _) in enumerate(tareas)}       # hora -> posición
    horario = np.full((len(tareas), y1 - y0, x1 - x0), np.nan, dtype="float32")
    t0 = time.time()
    with Pool(workers) as p:
        for n, (t, a) in enumerate(p.imap_unordered(leer_hora, tareas), 1):
            if a is not None:
                horario[pos[t]] = a
            if n % 24 == 0:
                print(f"  {anio}-{mes:02d}: {n}/{len(tareas)} h ({(time.time()-t0)/n:.1f} s/h)", flush=True)
    horario = horario.reshape(len(ds_mes), 24, y1 - y0, x1 - x0)
    n_horas = np.isfinite(horario).all(axis=(2, 3)).sum(axis=1).astype("int8")
    pr = np.nansum(horario, axis=1)
    pr[n_horas == 0] = np.nan
    ds = xr.Dataset(
        {"pr": (("time", "south_north", "west_east"), pr.astype("float32"),
                {"units": "mm/day", "long_name": "precipitación diaria acumulada",
                 "fuente": f"WRF-SAAG {VAR}, suma de 24 valores horarios"}),
         "n_horas": (("time",), n_horas, {"long_name": "horas válidas en el día (24 = completo)"})},
        coords={"time": pd.DatetimeIndex(ds_mes),
                "XLAT": (("south_north", "west_east"), malla["XLAT"].values),
                "XLONG": (("south_north", "west_east"), malla["XLONG"].values)},
        attrs={"dia_pluviometrico": f"día D = [D {DIA_INICIO_UTC:02d} UTC, D+1 {DIA_INICIO_UTC:02d} UTC)",
               "caja_indices": f"y[{y0}:{y1}] x[{x0}:{x1}]"})
    ds.to_netcdf(f, encoding={"pr": {"zlib": True, "complevel": 4}})
    inc = int((n_horas < 24).sum())
    print(f"Guardado {f.name}: {len(ds_mes)} días, {inc} incompletos, {time.time()-t0:.0f} s", flush=True)
    return f


def extraer_anio(anio, workers):
    caja = indices_caja()
    malla = xr.open_dataset(SALIDA / "malla_ucayali.nc")
    archivos = [extraer_mes(anio, m, caja, malla, workers) for m in MESES]
    ds = xr.concat([xr.open_dataset(f) for f in archivos], dim="time").load()
    if "HGT" in malla:
        ds["HGT"] = (("south_north", "west_east"), malla["HGT"].values, {"units": "m"})
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / f"saag_pr_diaria_{PERIODO}_{anio}.nc"
    ds.to_netcdf(out, encoding={"pr": {"zlib": True, "complevel": 4}})
    print(f"Listo: {out}  ({ds.sizes['time']} días)")


if __name__ == "__main__":
    args = sys.argv[1:]
    workers = WORKERS
    if "--workers" in args:
        i = args.index("--workers"); workers = int(args[i + 1]); del args[i:i + 2]
    arg = args[0] if args else "prueba"
    prueba(workers) if arg == "prueba" else extraer_anio(int(arg), workers)
