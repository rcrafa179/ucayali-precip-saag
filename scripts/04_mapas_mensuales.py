"""Mapas mensuales de precipitación SAAG (FMA) sobre el dominio del Ucayali bajo.

Uso:
    python scripts/04_mapas_mensuales.py            # usa todos los años que haya en data/processed/
    python scripts/04_mapas_mensuales.py 2015       # solo esos años

Lee data/processed/saag_pr_diaria_FMA_<año>.nc y escribe en figures/:
    mapas_total_<año>.png        acumulado mensual (mm/mes), Feb | Mar | Abr
    mapas_diaslluvia_<año>.png   días con lluvia (>= UMBRAL_DIA mm), Feb | Mar | Abr
    mapas_total_comparacion.png  años x meses (solo si hay 2 o más años)
    mapas_resumen_mensual.csv    promedio del dominio por año y mes
Los días con menos de 24 horas válidas no entran en los acumulados (se avisa).
"""
import sys
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import PROCESSED, FIGURAS, PERIODO, MESES, ANIOS

UMBRAL_DIA = 1.0   # mm/día para contar un día como lluvioso
NOMBRES = {2: "Febrero", 3: "Marzo", 4: "Abril"}
CIUDADES = {"Nauta": (-4.50, -73.58), "Requena": (-5.06, -73.85)}   # referencia aproximada


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
    """Devuelve dict mes -> (total mm, días lluviosos, n días válidos)."""
    out = {}
    for m in MESES:
        pr = ds.pr.sel(time=ds.time.dt.month == m)
        validos = int(pr.notnull().any(dim=("south_north", "west_east")).sum())
        out[m] = (pr.sum("time", skipna=True).where(validos > 0),
                  (pr >= UMBRAL_DIA).sum("time").where(validos > 0), validos)
    return out


def _eje(ax, ds, titulo):
    ax.set_title(titulo, fontsize=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25, lw=0.5)
    for n, (la, lo) in CIUDADES.items():
        if ds.XLAT.min() <= la <= ds.XLAT.max() and ds.XLONG.min() <= lo <= ds.XLONG.max():
            ax.plot(lo, la, "k^", ms=5)
            ax.annotate(n, (lo, la), xytext=(3, 3), textcoords="offset points", fontsize=7)


def fig_mapas(ds, datos, idx, anio, titulo, etiqueta, archivo, cmap, vmax=None):
    fig, axs = plt.subplots(1, len(MESES), figsize=(4.2 * len(MESES) + 1, 4.4), sharey=True)
    vmax = vmax or max(float(datos[m][idx].max()) for m in MESES)
    for ax, m in zip(np.atleast_1d(axs), MESES):
        h = ax.pcolormesh(ds.XLONG, ds.XLAT, datos[m][idx], cmap=cmap, vmin=0, vmax=vmax, shading="auto")
        _eje(ax, ds, f"{NOMBRES[m]} {anio}  ({datos[m][2]} días)")
        ax.set_xlabel("Longitud (°)")
    np.atleast_1d(axs)[0].set_ylabel("Latitud (°)")
    fig.colorbar(h, ax=axs, shrink=0.85, label=etiqueta)
    fig.suptitle(titulo + f" — WRF-SAAG 4 km, {anio}", fontsize=12)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / archivo, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {archivo}")


def main(anios):
    resumen, todos = [], {}
    for a in anios:
        ds = cargar(a)
        if ds is None:
            print(f"{a}: no hay data/processed/saag_pr_diaria_{PERIODO}_{a}.nc, salto")
            continue
        print(a)
        d = mensual(ds); todos[a] = (ds, d)
        fig_mapas(ds, d, 0, a, "Precipitación acumulada mensual", "mm / mes", f"mapas_total_{a}.png", "YlGnBu")
        fig_mapas(ds, d, 1, a, f"Días con lluvia (≥ {UMBRAL_DIA:g} mm)", "días", f"mapas_diaslluvia_{a}.png", "PuBu")
        for m in MESES:
            resumen.append(dict(anio=a, mes=m, dias_validos=d[m][2],
                                total_medio_mm=float(d[m][0].mean()), total_min_mm=float(d[m][0].min()),
                                total_max_mm=float(d[m][0].max()), dias_lluvia_medio=float(d[m][1].mean())))
    if not todos:
        sys.exit("No se encontró ningún archivo procesado.")
    if len(todos) > 1:
        vmax = max(float(d[m][0].max()) for _, d in todos.values() for m in MESES)
        fig, axs = plt.subplots(len(todos), len(MESES), figsize=(4 * len(MESES) + 1, 3.6 * len(todos)),
                                sharex=True, sharey=True, squeeze=False)
        for i, (a, (ds, d)) in enumerate(todos.items()):
            for j, m in enumerate(MESES):
                h = axs[i, j].pcolormesh(ds.XLONG, ds.XLAT, d[m][0], cmap="YlGnBu", vmin=0, vmax=vmax, shading="auto")
                _eje(axs[i, j], ds, f"{NOMBRES[m]} {a}")
        fig.colorbar(h, ax=axs, shrink=0.8, label="mm / mes")
        fig.suptitle("Precipitación acumulada mensual — WRF-SAAG 4 km", fontsize=12)
        fig.savefig(FIGURAS / "mapas_total_comparacion.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        print("  mapas_total_comparacion.png")
    tabla = pd.DataFrame(resumen).round(1)
    tabla.to_csv(FIGURAS / "mapas_resumen_mensual.csv", index=False)
    print("\nPromedio del dominio:\n", tabla.to_string(index=False))


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or ANIOS)
