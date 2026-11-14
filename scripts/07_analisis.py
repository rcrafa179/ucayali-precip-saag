"""Análisis de los resultados SAAG FMA sobre la Intercuenca 49911 (todos los años en data/processed/).

Uso:
    python scripts/07_analisis.py                  # WRF-SAAG
    python scripts/07_analisis.py --fuente pisco   # lo mismo con PISCO (archivos con prefijo pisco_)

Escribe en figures/ (con --fuente X, los nombres llevan el prefijo X_):
    <fuente>_diaria_cuenca_<año>.csv   serie DIARIA de la cuenca: media, mediana, mín./máx. por celda,
                                        % de la cuenca con lluvia (>= 1 mm) y días completos
    analisis_serie_diaria.png     lluvia diaria media de la cuenca, un panel por año
    analisis_anomalia_FMA.png     acumulado FMA de cada año menos el promedio de los años
    analisis_intensidad.png       distribución de la lluvia diaria (celdas con lluvia) por año
    analisis_resumen_FMA.csv      totales, días lluviosos, intensidad y extremos por año
"""
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import importlib.util as u
from pathlib import Path

from config import PROCESSED, FIGURAS, PERIODO, ANIOS, RAIZ

s = u.spec_from_file_location("mapas", Path(__file__).with_name("04_mapas_mensuales.py"))
mapas = u.module_from_spec(s); s.loader.exec_module(mapas)

UMBRAL = 1.0
COLOR = {2005: "#4292c6", 2010: "#e6550d", 2015: "#31a354"}


ETQ = "WRF-SAAG 4 km"


def main():
    geom, nombre = mapas.cargar_cuenca(None)
    datos = {a: mapas.cargar(a) for a in ANIOS}
    datos = {a: d for a, d in datos.items() if d is not None}
    ds0 = next(iter(datos.values()))
    mask = mapas.mascara_celdas(ds0, geom)
    print(f"{nombre}: {int(mask.sum())} celdas, años {list(datos)}")

    filas, serie, totales = [], {}, {}
    for a, ds in datos.items():
        pr = ds.pr.values[:, mask]                       # (días, celdas)
        media = np.nanmean(pr, axis=1)                   # lluvia diaria media de la cuenca
        serie[a] = pd.Series(media, index=pd.DatetimeIndex(ds.time.values))
        tot = np.nansum(ds.pr.values, axis=0)
        tot[~mask] = np.nan
        totales[a] = tot
        with np.errstate(all="ignore"):
            diaria = pd.DataFrame({
                "fecha": pd.DatetimeIndex(ds.time.values).strftime("%Y-%m-%d"),
                "pr_media_cuenca_mm": media,
                "pr_mediana_celdas_mm": np.nanmedian(pr, axis=1),
                "pr_min_celda_mm": np.nanmin(pr, axis=1),
                "pr_max_celda_mm": np.nanmax(pr, axis=1),
                "pct_cuenca_con_lluvia": 100 * (pr >= UMBRAL).sum(axis=1) / np.isfinite(pr).sum(axis=1),
                "dia_completo": np.isfinite(media),
            }).round(2)
        diaria.attrs = {}
        nom = f"{mapas.FUENTE}_diaria_cuenca_{a}.csv"
        diaria.to_csv(FIGURAS / nom, index=False)
        print(f"  {nom}")
        moj = pr[pr >= UMBRAL]
        filas.append(dict(
            anio=a,
            total_FMA_mm=np.nansum(media),
            total_FMA_min_celda=np.nanmin(tot[mask]), total_FMA_max_celda=np.nanmax(tot[mask]),
            dias_lluvia_cuenca=int((media >= UMBRAL).sum()),
            dias_lluvia_por_celda=float((pr >= UMBRAL).sum(axis=0).mean()),
            intensidad_mm_dia=moj.mean(),
            p95_mm_dia=np.percentile(moj, 95),
            max_celda_mm_dia=np.nanmax(pr),
            dia_max_cuenca=serie[a].idxmax().date().isoformat(), max_cuenca_mm=serie[a].max(),
            dias_cuenca_mayor_20mm=int((media >= 20).sum()),
            frac_lluvia_en_top10pct_dias=np.sort(media)[::-1][:max(1, len(media) // 10)].sum() / np.nansum(media),
        ))
    tabla = pd.DataFrame(filas).round(2)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(FIGURAS / mapas.pref("analisis_resumen_FMA.csv"), index=False)
    print(tabla.T.to_string())

    # serie diaria
    fig, axs = plt.subplots(len(serie), 1, figsize=(10, 2.3 * len(serie)), sharey=True)
    for ax, (a, sr) in zip(np.atleast_1d(axs), serie.items()):
        ax.bar(sr.index, sr.values, width=0.8, color=COLOR.get(a, "0.4"))
        ax.plot(sr.index, sr.rolling(7, center=True).mean(), color="k", lw=1.2, label="media móvil 7 días")
        ax.set_title(f"{a}: {sr.sum():.0f} mm en FMA", fontsize=10, loc="left")
        ax.set_ylabel("mm/día"); ax.grid(axis="y", alpha=0.3, lw=0.5)
        ax.margins(x=0.01)
    np.atleast_1d(axs)[0].legend(frameon=False, fontsize=8)
    fig.suptitle(f"Lluvia diaria media sobre la {nombre} — {ETQ}", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURAS / mapas.pref("analisis_serie_diaria.png"), dpi=150); plt.close(fig)

    # anomalía del acumulado FMA respecto al promedio de los años
    clim = np.mean(list(totales.values()), axis=0)
    anom = {a: 100 * (t - clim) / clim for a, t in totales.items()}
    lim = np.nanpercentile(np.abs(np.concatenate([v[mask] for v in anom.values()])), 98)
    fig, axs = plt.subplots(1, len(anom), figsize=(4.6 * len(anom) + 0.8, 5.4), sharey=True, squeeze=False)
    for ax, (a, v) in zip(axs[0], anom.items()):
        h = ax.pcolormesh(ds0.XLONG.values, ds0.XLAT.values, np.ma.masked_invalid(v), cmap="BrBG",
                          vmin=-lim, vmax=lim, shading="nearest")
        mapas.dibujar_contorno(ax, geom)
        ax.set_title(f"{a}  (cuenca: {100 * (np.nanmean(totales[a][mask]) / np.nanmean(clim[mask]) - 1):+.0f} %)", fontsize=11)
        ax.set_aspect("equal")
    cb = fig.colorbar(h, ax=list(axs[0]), orientation="horizontal", fraction=0.05, pad=0.1, shrink=0.7, extend="both")
    cb.set_label("Anomalía del acumulado FMA respecto al promedio 2005–2010–2015 (%)")
    fig.suptitle(f"Anomalía de precipitación FMA — {nombre}, {ETQ}", fontsize=13, y=1.02)
    fig.savefig(FIGURAS / mapas.pref("analisis_anomalia_FMA.png"), dpi=150, bbox_inches="tight"); plt.close(fig)

    # distribución de intensidades
    fig, ax = plt.subplots(figsize=(8, 4.4))
    bordes = np.logspace(0, np.log10(300), 30)
    for a, ds in datos.items():
        pr = ds.pr.values[:, mask].ravel()
        pr = pr[pr >= UMBRAL]
        ax.hist(pr, bins=bordes, density=True, histtype="step", lw=2, color=COLOR.get(a, "0.4"), label=str(a))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(f"Lluvia diaria en una celda ({ETQ}; días ≥ 1 mm), mm/día"); ax.set_ylabel("Densidad")
    ax.grid(alpha=0.3, lw=0.5, which="both"); ax.legend(frameon=False)
    ax.set_title(f"Distribución de la lluvia diaria — {nombre}, FMA", fontsize=11)
    fig.savefig(FIGURAS / mapas.pref("analisis_intensidad.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
    print("figuras: analisis_serie_diaria.png, analisis_anomalia_FMA.png, analisis_intensidad.png")


if __name__ == "__main__":
    import sys
    if "--fuente" in sys.argv:
        mapas.FUENTE = sys.argv[sys.argv.index("--fuente") + 1]
        ETQ = mapas.ETIQUETA.get(mapas.FUENTE, mapas.FUENTE)
    main()
