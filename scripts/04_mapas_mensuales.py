"""Mapas mensuales de precipitación SAAG (FMA) sobre el dominio del Ucayali bajo.

Uso:
    python scripts/04_mapas_mensuales.py                      # todos los años de data/processed/
    python scripts/04_mapas_mensuales.py 2015 2010            # solo esos años
    python scripts/04_mapas_mensuales.py --shp ruta/cuenca.shp --nombre "Intercuenca 49911"

Si se da una cuenca (--shp, o el primer .shp que haya en data/aux/), los mapas muestran solo las
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

from config import PROCESSED, FIGURAS, AUX, PERIODO, MESES, ANIOS

UMBRAL_DIA = 1.0     # mm/día para contar un día como lluvioso
CMAP = "RdPu"
NOMBRES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio",
           8: "Agosto", 9: "Setiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}


# ---------------------------------------------------------------- cuenca
def cargar_cuenca(shp):
    """Devuelve (geometría única en lon/lat, nombre por defecto) o (None, None)."""
    if shp is None:
        cand = sorted(AUX.glob("*.shp")) if AUX.exists() else []
        if not cand:
            return None, None
        shp = cand[0]
    import geopandas as gpd
    g = gpd.read_file(shp)
    if g.crs is not None and g.crs.to_epsg() != 4326:
        g = g.to_crs(4326)
    print(f"Cuenca: {shp}  ({len(g)} polígono/s)")
    return g.geometry.union_all() if hasattr(g.geometry, "union_all") else g.unary_union, shp.stem


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
def cargar(anio):
    f = PROCESSED / f"saag_pr_diaria_{PERIODO}_{anio}.nc"
    if not f.exists():
        return None
    ds = xr.open_dataset(f).load()
    malos = int((ds.n_horas < 24).sum())
    if malos:
        print(f"  aviso {anio}: {malos} días con horas faltantes, se excluyen de los acumulados")
    return ds.where(ds.n_horas == 24)


def mensual(ds):
    """dict mes -> (total mm, días lluviosos) como arrays 2D."""
    out = {}
    for m in MESES:
        pr = ds.pr.sel(time=ds.time.dt.month == m)
        out[m] = (pr.sum("time", skipna=True).values, (pr >= UMBRAL_DIA).sum("time").values)
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
        h = ax.pcolormesh(ds.XLONG.values, ds.XLAT.values, np.ma.masked_where(~mask, c),
                          cmap=CMAP, vmin=vmin, vmax=vmax, shading="nearest")
        if geom is not None:
            dibujar_contorno(ax, geom)
        ax.set_title(NOMBRES[m] + (f" {subt}" if subt else ""), fontsize=12)
        ax.set_aspect("equal")
        ax.set_xlim(float(ds.XLONG.min()), float(ds.XLONG.max()))
        ax.set_ylim(float(ds.XLAT.min()), float(ds.XLAT.max()))
    cb = fig.colorbar(h, ax=list(axs), orientation="horizontal", fraction=0.05, pad=0.1, shrink=0.75)
    cb.set_label(etiqueta)
    fig.suptitle(titulo, fontsize=14)
    FIGURAS.mkdir(parents=True, exist_ok=True)
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
            print(f"{a}: no hay data/processed/saag_pr_diaria_{PERIODO}_{a}.nc, salto")
            continue
        if mask is None:
            mask = mascara_celdas(ds, geom) if geom is not None else np.ones(ds.XLAT.shape, bool)
            print(f"Celdas mostradas: {int(mask.sum())} de {mask.size}")
        todos[a] = (ds, mensual(ds))
    if not todos:
        sys.exit("No se encontró ningún archivo procesado.")
    ds0 = next(iter(todos.values()))[0]

    print("Climatología")
    clim = {m: np.mean([d[m][0] for _, d in todos.values()], axis=0) for m in MESES}
    lista = ", ".join(map(str, todos))
    figura(ds0, clim, mask, geom, f"Mapa climatológico mensual de precipitación{sufijo}\nWRF-SAAG 4 km, promedio de {lista}",
           "Precipitación (mm/mes)", "mapas_climatologia.png")
    for a, (ds, d) in todos.items():
        print(a)
        figura(ds0, {m: d[m][0] for m in MESES}, mask, geom, f"Precipitación acumulada mensual{sufijo}\nWRF-SAAG 4 km, {a}",
               "Precipitación (mm/mes)", f"mapas_total_{a}.png")
        figura(ds0, {m: d[m][1] for m in MESES}, mask, geom, f"Días con lluvia (≥ {UMBRAL_DIA:g} mm){sufijo}\nWRF-SAAG 4 km, {a}",
               "días", f"mapas_diaslluvia_{a}.png")
        for m in MESES:
            t = d[m][0][mask]
            resumen.append(dict(anio=a, mes=m, total_medio_mm=t.mean(), total_min_mm=t.min(), total_max_mm=t.max(),
                                dias_lluvia_medio=d[m][1][mask].mean()))
    tabla = pd.DataFrame(resumen).round(1)
    tabla.to_csv(FIGURAS / "mapas_resumen_mensual.csv", index=False)
    print("\nPromedio sobre las celdas mostradas:\n", tabla.to_string(index=False))


if __name__ == "__main__":
    args = sys.argv[1:]
    opc = {}
    for k in ("--shp", "--nombre"):
        if k in args:
            i = args.index(k); opc[k] = args[i + 1]; del args[i:i + 2]
    from pathlib import Path
    main([int(x) for x in args] or ANIOS, Path(opc["--shp"]) if "--shp" in opc else None, opc.get("--nombre"))
