"""Mapas mensuales de precipitación SAAG (FMA) sobre el dominio del Ucayali bajo.

Uso:
    python scripts/04_mapas_mensuales.py                      # todos los años de data/processed/
    python scripts/04_mapas_mensuales.py 2015 2010            # solo esos años
    python scripts/04_mapas_mensuales.py --shp ruta/cuenca.shp --nombre "Intercuenca 49911"
    python scripts/04_mapas_mensuales.py --fuente wrfctrl    # corridas locales (ver 05_wrf_ctrl.py)

Con --fuente X lee data/processed/X_pr_diaria_FMA_<año>.nc y antepone "X_" a las figuras (salvo saag).
Si la cuenca no cae dentro del dominio, se ignora y se muestra todo el dominio. Si el dominio tiene
relieve (> 1000 m de desnivel) se dibujan curvas de nivel de 500, 1500 y 3000 m.

Si se da una cuenca (--shp, o por defecto el .shp de cuenca/ — Intercuenca 49911 — o de data/aux/), los mapas muestran solo las
celdas de 4 km que tocan la cuenca (el resto en blanco) y dibujan su contorno. Sin cuenca se
muestra todo el dominio.

Lee data/processed/saag_pr_diaria_FMA_<año>.nc y escribe en figures/ (mismo estilo en todos):
    mapas_climatologia.png        promedio de los años disponibles, Feb | Mar | Abr  (mm/mes)
    mapas_total_<año>.png         acumulado mensual de cada año
    mapas_diaslluvia_<año>.png    días con lluvia (>= UMBRAL_DIA mm) de cada año
    mapas_resumen_mensual.csv     promedio sobre la cuenca (o dominio) por año y mes
Los días con menos de 24 horas válidas no entran en los acumulados (se avisa).
"""
import sys
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import PROCESSED, FIGURAS, AUX, RAIZ, PERIODO, MESES, ANIOS

UMBRAL_DIA = 1.0     # mm/día para contar un día como lluvioso
CMAP = "RdPu"
NOMBRES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio",
           8: "Agosto", 9: "Setiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}


# ---------------------------------------------------------------- cuenca
def leer_shp(shp):
    """Lector mínimo de shapefiles de polígonos (sin geopandas/pyogrio, que a veces chocan con PROJ).
    Supone coordenadas lon/lat (WGS84), como el shapefile incluido en cuenca/."""
    import struct
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    d = open(shp, "rb").read()
    pos, anillos = 100, []
    while pos + 8 <= len(d):
        n = struct.unpack(">i", d[pos + 4:pos + 8])[0] * 2
        rec = d[pos + 8:pos + 8 + n]; pos += 8 + n
        if struct.unpack("<i", rec[:4])[0] not in (5, 15, 25):
            continue
        nparts, npts = struct.unpack("<2i", rec[36:44])
        partes = list(struct.unpack(f"<{nparts}i", rec[44:44 + 4 * nparts])) + [npts]
        xy = np.frombuffer(rec, "<f8", 2 * npts, 44 + 4 * nparts).reshape(npts, 2)
        anillos += [xy[a:b] for a, b in zip(partes[:-1], partes[1:])]
    ext, hue = [], []
    for r in anillos:   # anillo horario = exterior, antihorario = hueco
        area = 0.5 * np.sum(r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1])
        (ext if area < 0 else hue).append(Polygon(r))
    geom = unary_union(ext)
    for h in hue:
        geom = geom.difference(h)
    return geom


def nombre_dbf(shp):
    """Campo NOMBRE del primer registro del .dbf, o el nombre del archivo si no se puede leer."""
    import struct
    try:
        d = open(shp.with_suffix(".dbf"), "rb").read()
        nrec, hlen, rlen = struct.unpack("<IHH", d[4:12])
        campos, off, k = [], 1, 32
        while d[k] != 0x0D:
            campos.append((d[k:k + 11].split(b"\0")[0].decode(), d[k + 16], off)); off += d[k + 16]; k += 32
        for nom, ln, o in campos:
            if nom == "NOMBRE":
                return d[hlen + o:hlen + o + ln].decode("latin-1").strip()
    except Exception:
        pass
    return shp.stem


def cargar_cuenca(shp):
    """Devuelve (geometría única en lon/lat, nombre) o (None, None)."""
    if shp is None:   # por defecto: cuenca/*.shp del repo (Intercuenca 49911), luego data/aux/
        cand = [f for d in (RAIZ / "cuenca", AUX) if d.exists() for f in sorted(d.glob("*.shp"))]
        if not cand:
            return None, None
        shp = cand[0]
    print(f"Cuenca: {shp}")
    return leer_shp(shp), nombre_dbf(shp)


def mascara_celdas(ds, geom):
    """True en las celdas de 4 km (cuadrado alrededor del centro) que intersectan la cuenca."""
    from shapely.geometry import box
    lat, lon = ds.XLAT.values, ds.XLONG.values
    dy = np.abs(np.gradient(lat, axis=0)).mean() / 2
    dx = np.abs(np.gradient(lon, axis=1)).mean() / 2
    m = np.zeros(lat.shape, bool)
    for i in range(lat.shape[0]):
        for j in range(lat.shape[1]):
            m[i, j] = geom.intersects(box(lon[i, j] - dx, lat[i, j] - dy, lon[i, j] + dx, lat[i, j] + dy))
    return m


def dibujar_contorno(ax, geom):
    for pol in getattr(geom, "geoms", [geom]):
        ax.plot(*pol.exterior.xy, color="k", lw=0.8)
        for h in pol.interiors:
            ax.plot(*h.xy, color="k", lw=0.5)


# ---------------------------------------------------------------- datos
FUENTE = "saag"
ETIQUETA = {"saag": "WRF-SAAG 4 km", "wrfctrl": "WRF-SAAG 4 km (dominio WRF2d_CTRL)"}


def pref(nombre):
    return nombre if FUENTE == "saag" else f"{FUENTE}_{nombre}"


def cargar(anio):
    f = PROCESSED / f"{FUENTE}_pr_diaria_{PERIODO}_{anio}.nc"
    if not f.exists():
        return None
    ds = xr.open_dataset(f).load()
    hgt = ds["HGT"].values if "HGT" in ds else None
    ds = ds.drop_vars([v for v in ("HGT", "LANDMASK") if v in ds])
    malos = int((ds.n_horas < 24).sum())
    if malos:
        print(f"  aviso {anio}: {malos} días con horas faltantes, se excluyen de los acumulados")
    ds = ds.where(ds.n_horas == 24)
    ds.attrs["_hgt"] = hgt
    return ds


def mensual(ds):
    """dict mes -> (total mm, días lluviosos) como arrays 2D."""
    out = {}
    for m in MESES:
        pr = ds.pr.sel(time=ds.time.dt.month == m)
        out[m] = (pr.sum("time", skipna=True, min_count=1).values,
                  (pr >= UMBRAL_DIA).sum("time").where(pr.notnull().any("time")).values)
    return out


# ---------------------------------------------------------------- figura
def figura(ds, campos, mask, geom, titulo, etiqueta, archivo, subt=None):
    """campos: dict mes -> array 2D. Un panel por mes, escala común, colorbar horizontal abajo."""
    n = len(campos)
    vals = np.concatenate([np.where(mask, c, np.nan).ravel() for c in campos.values()])
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    fig, axs = plt.subplots(1, n, figsize=(4.6 * n + 0.8, 5.6), sharey=True, squeeze=False)
    axs = axs[0]
    for ax, (m, c) in zip(axs, campos.items()):
        h = ax.pcolormesh(ds.XLONG.values, ds.XLAT.values, np.ma.masked_where(~mask | ~np.isfinite(c), c),
                          cmap=CMAP, vmin=vmin, vmax=vmax, shading="nearest")
        if geom is not None:
            dibujar_contorno(ax, geom)
        if geom is None and not np.isfinite(c).all():     # datos con máscara propia: dibujar su borde
            ax.contour(ds.XLONG.values, ds.XLAT.values, np.isfinite(c).astype(float), levels=[0.5],
                       colors="k", linewidths=0.8)
        hgt = ds.attrs.get("_hgt")
        if hgt is not None and np.nanmax(hgt) - np.nanmin(hgt) > 1000:
            cs = ax.contour(ds.XLONG.values, ds.XLAT.values, hgt, levels=[500, 1500, 3000],
                            colors="0.25", linewidths=[0.5, 0.6, 0.8])
            ax.clabel(cs, fontsize=6, fmt="%d m")
        ax.set_title(NOMBRES[m] + (f" {subt}" if subt else ""), fontsize=12)
        ax.set_aspect("equal")
        ax.set_xlim(float(ds.XLONG.min()), float(ds.XLONG.max()))
        ax.set_ylim(float(ds.XLAT.min()), float(ds.XLAT.max()))
    cb = fig.colorbar(h, ax=list(axs), orientation="horizontal", fraction=0.05, pad=0.1, shrink=0.75)
    cb.set_label(etiqueta)
    fig.suptitle(titulo, fontsize=14)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    archivo = pref(archivo)
    fig.savefig(FIGURAS / archivo, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {archivo}")


def main(anios, shp=None, nombre=None):
    geom, nom_shp = cargar_cuenca(shp)
    nombre = nombre or nom_shp
    sufijo = f" - {nombre}" if nombre else ""
    todos, resumen, mask = {}, [], None
    for a in anios:
        ds = cargar(a)
        if ds is None:
            print(f"{a}: no hay data/processed/{FUENTE}_pr_diaria_{PERIODO}_{a}.nc, salto")
            continue
        if mask is None:
            mask = mascara_celdas(ds, geom) if geom is not None else np.ones(ds.XLAT.shape, bool)
            if not mask.any():
                print("  la cuenca no cae dentro de este dominio: se ignora y se muestra todo el dominio")
                geom, sufijo, mask = None, "", np.ones(ds.XLAT.shape, bool)
            print(f"Celdas mostradas: {int(mask.sum())} de {mask.size}")
        todos[a] = (ds, mensual(ds))
    if not todos:
        sys.exit("No se encontró ningún archivo procesado.")
    ds0 = next(iter(todos.values()))[0]

    print("Climatología")
    clim = {m: np.mean([d[m][0] for _, d in todos.values()], axis=0) for m in MESES}
    lista = ", ".join(map(str, todos))
    figura(ds0, clim, mask, geom, f"Mapa climatológico mensual de precipitación{sufijo}\n{ETIQUETA.get(FUENTE, FUENTE)}, promedio de {lista}",
           "Precipitación (mm/mes)", "mapas_climatologia.png")
    for a, (ds, d) in todos.items():
        print(a)
        figura(ds0, {m: d[m][0] for m in MESES}, mask, geom, f"Precipitación acumulada mensual{sufijo}\n{ETIQUETA.get(FUENTE, FUENTE)}, {a}",
               "Precipitación (mm/mes)", f"mapas_total_{a}.png")
        figura(ds0, {m: d[m][1] for m in MESES}, mask, geom, f"Días con lluvia (≥ {UMBRAL_DIA:g} mm){sufijo}\n{ETIQUETA.get(FUENTE, FUENTE)}, {a}",
               "días", f"mapas_diaslluvia_{a}.png")
        for m in MESES:
            t = d[m][0][mask]
            resumen.append(dict(anio=a, mes=m, total_medio_mm=np.nanmean(t), total_min_mm=np.nanmin(t),
                                total_max_mm=np.nanmax(t), dias_lluvia_medio=np.nanmean(d[m][1][mask])))
    tabla = pd.DataFrame(resumen).round(1)
    tabla.to_csv(FIGURAS / pref("mapas_resumen_mensual.csv"), index=False)
    print("\nPromedio sobre las celdas mostradas:\n", tabla.to_string(index=False))


if __name__ == "__main__":
    args = sys.argv[1:]
    opc = {}
    for k in ("--shp", "--nombre", "--fuente"):
        if k in args:
            i = args.index(k); opc[k] = args[i + 1]; del args[i:i + 2]
    from pathlib import Path
    FUENTE = opc.get("--fuente", "saag")
    main([int(x) for x in args] or ANIOS, Path(opc["--shp"]) if "--shp" in opc else None, opc.get("--nombre"))
