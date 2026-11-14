"""
Extracción remota de precipitación horaria WRF-SAAG (NCAR GDEX d616000)
para la cuenca del Ucayali. Lee vía OPeNDAP SOLO la caja de la cuenca,
sin descargar los archivos completos (~700 MB/hora, todo el continente).

Uso (desde la raíz del repo):
    python scripts/01_extraer_saag.py prueba            # lee 1 hora, muestra variables y tiempo
    python scripts/01_extraer_saag.py 2005              # extrae el año completo (reanudable)

Salida: data/raw/saag/<año>/saag_prec_<YYYYMM>.nc  (un archivo por mes)

ANTES DE CORRER:
 1. Abre en el navegador el catálogo THREDDS:
      https://tds.gdex.ucar.edu/thredds/catalog/files/g/d616000/catalog.html
    y navega hasta un archivo 2D horario (wrf2d_d01_YYYY-MM-DD_HHMMSS.nc).
    Ajusta RUTA_2D abajo según la estructura de carpetas real.
 2. Corre el modo "prueba" y revisa el nombre de la variable de precipitación.
"""
import sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
from config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, RAW_SAAG

# ---------------- CONFIGURACIÓN ----------------
BASE = "https://tds.gdex.ucar.edu/thredds/dodsC/files/g/d616000"
URL_CONST = f"{BASE}/INVARIANT/wrfconstants_SAAG.nc"

# Plantilla de ruta de los archivos 2D horarios. VERIFICAR en el catálogo:
# la carpeta podría ser por mes (p.ej. "200501") o por año/mes.
RUTA_2D = "{yyyymm}/wrf2d_d01_{fecha}_{hhmmss}.nc"

# La caja del Ucayali está en config.py

# Variables candidatas de precipitación (se usa la primera que exista)
VARS_PREC = ["PREC_ACC_NC", "PREC_ACC_C", "RAINNC", "RAINC"]

SALIDA = RAW_SAAG
REINTENTOS = 4
# ------------------------------------------------


def indices_caja():
    """Calcula (y0,y1,x0,x1) de la caja a partir de XLAT/XLONG y guarda la malla."""
    f = SALIDA / "malla_ucayali.nc"
    if f.exists():
        m = xr.open_dataset(f)
        return tuple(int(m.attrs[k]) for k in ("y0", "y1", "x0", "x1"))
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
    sub.attrs.update(y0=int(y0), y1=int(y1), x0=int(x0), x1=int(x1))
    SALIDA.mkdir(parents=True, exist_ok=True)
    sub.to_netcdf(f)
    print(f"Caja: y[{y0}:{y1}] x[{x0}:{x1}] -> {y1-y0} x {x1-x0} puntos. Malla guardada en {f}")
    return y0, y1, x0, x1


def url_hora(t):
    return f"{BASE}/" + RUTA_2D.format(
        yyyymm=t.strftime("%Y%m"), fecha=t.strftime("%Y-%m-%d"), hhmmss=t.strftime("%H%M%S"))


def leer_hora(t, caja, var=None):
    y0, y1, x0, x1 = caja
    for intento in range(REINTENTOS):
        try:
            ds = xr.open_dataset(url_hora(t))
            if var is None:
                var = next(v for v in VARS_PREC if v in ds)
            da = ds[var]
            ydim, xdim = da.dims[-2:]
            out = da.isel({ydim: slice(y0, y1), xdim: slice(x0, x1)}).load()
            ds.close()
            return out.squeeze(drop=True).expand_dims(time=[t]), var
        except StopIteration:
            raise RuntimeError(f"No se encontró variable de precipitación. Variables: {list(ds.data_vars)}")
        except Exception as e:
            espera = 10 * (intento + 1)
            print(f"  {t} intento {intento+1} falló ({e}); reintento en {espera}s")
            time.sleep(espera)
    print(f"  !! {t} sin datos tras {REINTENTOS} intentos, se deja NaN")
    return None, var


def prueba():
    caja = indices_caja()
    t = pd.Timestamp("2005-01-15 18:00")
    print("URL:", url_hora(t))
    ds = xr.open_dataset(url_hora(t))
    print("Variables disponibles:", list(ds.data_vars))
    t0 = time.time()
    da, var = leer_hora(t, caja)
    print(f"Variable usada: {var} | unidades: {da.attrs.get('units')} | "
          f"descripción: {da.attrs.get('description')}")
    print(f"Forma: {da.shape} | min/max: {float(da.min()):.2f}/{float(da.max()):.2f}")
    dt = time.time() - t0
    print(f"Tiempo por hora: {dt:.1f}s -> ~{dt*8760/3600:.1f} h por año")
    print("Si la variable es RAINNC/RAINC (acumulada desde el inicio), hay que diferenciar hora a hora.")


def extraer_anio(anio):
    caja = indices_caja()
    var = None
    for mes in range(1, 13):
        f = SALIDA / str(anio) / f"saag_prec_{anio}{mes:02d}.nc"
        if f.exists():
            print(f"{f} ya existe, salto"); continue
        f.parent.mkdir(parents=True, exist_ok=True)
        horas = pd.date_range(f"{anio}-{mes:02d}-01", periods=pd.Timestamp(anio, mes, 1).days_in_month * 24, freq="h")
        trozos = []
        for t in horas:
            da, var = leer_hora(t, caja, var)
            if da is not None:
                trozos.append(da)
            if t.hour == 0:
                print(f"{t:%Y-%m-%d} ok")
        mes_da = xr.concat(trozos, "time").reindex(time=horas)  # horas faltantes -> NaN
        mes_da.name = "prec"
        mes_da.attrs["variable_original"] = var
        mes_da.attrs["tiempo"] = "UTC"
        mes_da.to_dataset().to_netcdf(f, encoding={"prec": {"zlib": True, "complevel": 4, "dtype": "float32"}})
        print(f"Guardado {f}  (faltantes: {int(mes_da.isnull().all(dim=mes_da.dims[1:]).sum())} h)")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "prueba"
    prueba() if arg == "prueba" else extraer_anio(int(arg))
