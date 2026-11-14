"""Descarga PISCOp v2.1 (SENAMHI) diario, versión "stable" (1981-2016), recortado a la cuenca y a FMA.

Fuente: IRI Data Library (Columbia University), que distribuye PISCOp v2.1 sin cuenta:
    https://iridl.ldeo.columbia.edu/SOURCES/.SENAMHI/.HSR/.PISCO/.Prec/.v2p1/.stable/.daily/
Variable Prec (mm/día), malla de 0.1°.

Uso (sin años = 2005, 2010 y 2015):
    python scripts/02b_descargar_pisco.py
    python scripts/02b_descargar_pisco.py 2010

Si la descarga falla (red de la universidad, proxy...), el script imprime la URL: ábrela en el navegador,
guarda el archivo como data/raw/pisco/pisco_pr_<año>.nc y sigue con 03_diario_obs.py pisco.

Se baja del 31-ene al 1-may para poder corregir un posible desfase de un día en la etiqueta de fecha
(ver PISCO_DESFASE_DIAS en config.py y la verificación que imprime 08_comparar.py pisco).
"""
import sys
import time
import urllib.request
from urllib.parse import quote

from config import RAW_PISCO, ANIOS, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX

BASE = "https://iridl.ldeo.columbia.edu/SOURCES/.SENAMHI/.HSR/.PISCO/.Prec/.v2p1/.stable/.daily/.Prec"
M = 0.15   # margen: celdas de 0.1° del borde que tocan la cuenca


def url(anio):
    rango = lambda eje, a, b: f"/{eje}/({a})/({b})/RANGEEDGES"
    t = rango("T", quote(f"31 Jan {anio}"), quote(f"1 May {anio}"))
    return (BASE + rango("X", round(LON_MIN - M, 2), round(LON_MAX + M, 2))
            + rango("Y", round(LAT_MIN - M, 2), round(LAT_MAX + M, 2)) + t + "/data.nc")


def descargar(anio):
    RAW_PISCO.mkdir(parents=True, exist_ok=True)
    f = RAW_PISCO / f"pisco_pr_{anio}.nc"
    if f.exists() and f.stat().st_size > 0:
        print(f"{f.name} ya existe, salto"); return
    u = url(anio)
    for intento in range(1, 4):
        try:
            print(f"Descargando PISCO {anio} (intento {intento}) ...", flush=True)
            req = urllib.request.Request(u, headers={"User-Agent": "ucayali-precip-saag"})
            with urllib.request.urlopen(req, timeout=300) as r:
                datos = r.read()
            if not datos.startswith((b"CDF", b"\x89HDF")):
                raise ValueError("la respuesta no es un NetCDF (IRIDL devolvió una página de error)")
            f.write_bytes(datos)
            print(f"  ok {f.name} ({len(datos) / 1e3:.0f} kB)")
            return
        except Exception as e:
            print(f"  falló: {e}")
            time.sleep(5 * intento)
    print(f"\nNo se pudo descargar {anio}. Abre esta URL en el navegador y guarda el archivo como {f}:\n{u}\n")


if __name__ == "__main__":
    for a in [int(x) for x in sys.argv[1:]] or ANIOS:
        descargar(a)
    print("Siguiente: python scripts/03_diario_obs.py pisco   y luego   python scripts/08_comparar.py pisco")
