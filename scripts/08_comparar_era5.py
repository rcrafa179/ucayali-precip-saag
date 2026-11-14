"""Compara la lluvia diaria FMA de WRF-SAAG (4 km) con ERA5 (0.25°) sobre la Intercuenca 49911.

Uso (después de 02_descargar_era5.py y 03_diario_obs.py era5):
    python scripts/08_comparar_era5.py              # todos los años con ambos archivos

Cómo se compara:
  - Media de la cuenca: SAAG = promedio de sus celdas de 4 km que tocan la cuenca; ERA5 = promedio de sus
    celdas de 0.25° ponderado por el área de cada celda que cae dentro de la cuenca.
  - Mapas: además del SAAG a 4 km, se muestra el SAAG promediado en la malla de ERA5 (mismas celdas de
    0.25°) para que la diferencia SAAG − ERA5 sea entre campos de la misma resolución.
  - Mismo día pluviométrico en ambos (config.DIA_INICIO_UTC).

Escribe en figures/:
    era5_comparacion_resumen.csv      totales, sesgo, correlación, RMSE, días lluviosos y extremos por año
    era5_comparacion_mensual.csv      acumulado mensual de la cuenca, SAAG y ERA5
    era5_comparacion_serie.png        series diarias de la cuenca, un panel por año
    era5_comparacion_mensual.png      barras mensuales SAAG vs ERA5
    era5_comparacion_dispersion.png   dispersión diaria y curva de frecuencias (días ≥ umbral)
    era5_comparacion_mapas.png        acumulado FMA: SAAG 4 km | SAAG en malla ERA5 | ERA5 | diferencia
"""
import sys
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import importlib.util as u
from pathlib import Path
from shapely.geometry import box

from config import PROCESSED, FIGURAS, PERIODO, ANIOS, MESES

s = u.spec_from_file_location("mapas", Path(__file__).with_name("04_mapas_mensuales.py"))
mapas = u.module_from_spec(s); s.loader.exec_module(mapas)

UMBRAL = 1.0
C_SAAG, C_ERA5 = "#7a0177", "#fd8d3c"
NOMBRES = {2: "Feb", 3: "Mar", 4: "Abr"}


def pesos_era5(lat, lon, geom):
    """Fracción del área de cada celda ERA5 (0.25°) que cae dentro de la cuenca."""
    dlat, dlon = abs(float(lat[1] - lat[0])) / 2, abs(float(lon[1] - lon[0])) / 2
    w = np.zeros((len(lat), len(lon)))
    for i, la in enumerate(lat):
        for j, lo in enumerate(lon):
            c = box(lo - dlon, la - dlat, lo + dlon, la + dlat)
            w[i, j] = c.intersection(geom).area / c.area
    return w


def saag_en_malla_era5(saag2d, slat, slon, lat, lon):
    """Promedio de las celdas SAAG cuyo centro cae en cada celda ERA5."""
    dlat, dlon = abs(float(lat[1] - lat[0])) / 2, abs(float(lon[1] - lon[0])) / 2
    out = np.full((len(lat), len(lon)), np.nan)
    for i, la in enumerate(lat):
        for j, lo in enumerate(lon):
            m = (np.abs(slat - la) <= dlat) & (np.abs(slon - lo) <= dlon) & np.isfinite(saag2d)
            if m.sum() >= 10:   # celda ERA5 bien cubierta por el dominio SAAG
                out[i, j] = saag2d[m].mean()
    return out


def cargar_era5(anio):
    f = PROCESSED / f"era5_pr_diaria_{PERIODO}_{anio}.nc"
    if not f.exists():
        return None
    e = xr.open_dataset(f).load()
    e = e.sortby("lat").sortby("lon")
    malos = int((e.n_pasos < 24).sum())
    if malos:
        print(f"  aviso ERA5 {anio}: {malos} días incompletos, se excluyen")
    return e.where(e.n_pasos == 24)


def main():
    geom, nombre = mapas.cargar_cuenca(None)
    res, filas, mens = {}, [], []
    mask = None
    for a in ANIOS:
        sg, er = mapas.cargar(a), cargar_era5(a)
        if sg is None or er is None:
            print(f"{a}: falta {'SAAG' if sg is None else 'ERA5'} en data/processed/, salto")
            continue
        if mask is None:
            mask = mapas.mascara_celdas(sg, geom)
            w = pesos_era5(er.lat.values, er.lon.values, geom)
            print(f"{nombre}: {int(mask.sum())} celdas SAAG; {int((w > 0).sum())} celdas ERA5 "
                  f"(área equivalente {w.sum():.1f} celdas)")
        ss = pd.Series(np.nanmean(sg.pr.values[:, mask], axis=1), index=pd.DatetimeIndex(sg.time.values))
        ep = er.pr.values
        ok = np.isfinite(ep)
        es = pd.Series(np.nansum(np.where(ok, ep, 0) * w, axis=(1, 2)) / (ok * w).sum(axis=(1, 2)),
                       index=pd.DatetimeIndex(er.time.values))
        ss, es = ss.align(es, join="inner")
        val = ss.notna() & es.notna()
        ss, es = ss[val], es[val]
        res[a] = dict(saag=ss, era5=es, sg=sg, er=er)
        filas.append(dict(
            anio=a, dias=len(ss),
            saag_FMA_mm=ss.sum(), era5_FMA_mm=es.sum(), sesgo_mm=ss.sum() - es.sum(),
            sesgo_pct=100 * (ss.sum() / es.sum() - 1),
            r_diaria=np.corrcoef(ss, es)[0, 1], rmse_diaria_mm=np.sqrt(((ss - es) ** 2).mean()),
            r_7dias=np.corrcoef(ss.rolling(7, center=True).mean().dropna(), es.rolling(7, center=True).mean().dropna())[0, 1],
            dias_lluvia_saag=int((ss >= UMBRAL).sum()), dias_lluvia_era5=int((es >= UMBRAL).sum()),
            dias_20mm_saag=int((ss >= 20).sum()), dias_20mm_era5=int((es >= 20).sum()),
            p95_saag=np.percentile(ss, 95), p95_era5=np.percentile(es, 95),
            max_saag=ss.max(), max_era5=es.max(),
        ))
        for m in MESES:
            mens.append(dict(anio=a, mes=m, saag_mm=ss[ss.index.month == m].sum(), era5_mm=es[es.index.month == m].sum()))
    if not res:
        sys.exit("No hay años con SAAG y ERA5. Corre antes 02_descargar_era5.py y 03_diario_obs.py era5.")

    FIGURAS.mkdir(parents=True, exist_ok=True)
    tabla = pd.DataFrame(filas).round(2)
    tabla.to_csv(FIGURAS / "era5_comparacion_resumen.csv", index=False)
    tm = pd.DataFrame(mens).round(1)
    tm["sesgo_pct"] = (100 * (tm.saag_mm / tm.era5_mm - 1)).round(0)
    tm.to_csv(FIGURAS / "era5_comparacion_mensual.csv", index=False)
    print(tabla.T.to_string()); print(tm.to_string(index=False))

    # series diarias
    fig, axs = plt.subplots(len(res), 1, figsize=(10, 2.4 * len(res)), sharey=True, squeeze=False)
    for ax, (a, r) in zip(axs[:, 0], res.items()):
        ax.bar(r["saag"].index, r["saag"].values, width=0.8, color=C_SAAG, alpha=0.55, label="WRF-SAAG 4 km")
        ax.plot(r["era5"].index, r["era5"].values, color=C_ERA5, lw=1.8, marker="o", ms=2.5, label="ERA5 0.25°")
        f = tabla.set_index("anio").loc[a]
        ax.set_title(f"{a}: SAAG {f.saag_FMA_mm:.0f} mm | ERA5 {f.era5_FMA_mm:.0f} mm | r diaria = {f.r_diaria:.2f}",
                     fontsize=10, loc="left")
        ax.set_ylabel("mm/día"); ax.grid(axis="y", alpha=0.3, lw=0.5); ax.margins(x=0.01)
    axs[0, 0].legend(frameon=False, fontsize=8, ncol=2)
    fig.suptitle(f"Lluvia diaria media de la {nombre}: WRF-SAAG vs ERA5", fontsize=12)
    fig.tight_layout(); fig.savefig(FIGURAS / "era5_comparacion_serie.png", dpi=150); plt.close(fig)

    # barras mensuales
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(tm)); wd = 0.38
    ax.bar(x - wd / 2, tm.saag_mm, wd, color=C_SAAG, label="WRF-SAAG 4 km")
    ax.bar(x + wd / 2, tm.era5_mm, wd, color=C_ERA5, label="ERA5 0.25°")
    ax.set_xticks(x, [f"{NOMBRES[m]}\n{a}" for a, m in zip(tm.anio, tm.mes)])
    for xi, (sv, ev) in enumerate(zip(tm.saag_mm, tm.era5_mm)):
        ax.text(xi, max(sv, ev) + 5, f"{100 * (sv / ev - 1):+.0f}%", ha="center", fontsize=8, color="0.3")
    ax.set_ylabel("mm/mes"); ax.grid(axis="y", alpha=0.3, lw=0.5); ax.legend(frameon=False)
    ax.set_title(f"Acumulado mensual de la {nombre} (etiqueta: sesgo de SAAG respecto a ERA5)", fontsize=11)
    fig.savefig(FIGURAS / "era5_comparacion_mensual.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # dispersión + curva de excedencia
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
    tope = max(max(r["saag"].max(), r["era5"].max()) for r in res.values()) * 1.05
    for a, r in res.items():
        a1.scatter(r["era5"], r["saag"], s=12, alpha=0.6, label=str(a))
    for nom, clave, col in (("WRF-SAAG 4 km", "saag", C_SAAG), ("ERA5 0.25°", "era5", C_ERA5)):
        v = np.sort(np.concatenate([r[clave].values for r in res.values()]))[::-1]   # todos los años juntos
        a2.plot(np.arange(1, len(v) + 1) / len(v) * 100, v, color=col, lw=2, label=nom)
    a1.plot([0, tope], [0, tope], "k--", lw=0.8); a1.set_xlim(0, tope); a1.set_ylim(0, tope)
    a1.set_xlabel("ERA5 (mm/día)"); a1.set_ylabel("WRF-SAAG (mm/día)"); a1.set_aspect("equal")
    a1.set_title("Lluvia diaria de la cuenca", fontsize=10); a1.legend(frameon=False, fontsize=8); a1.grid(alpha=0.3, lw=0.5)
    a2.set_xlabel("% de días en que se supera el valor"); a2.set_ylabel("mm/día")
    a2.set_title(f"Curva de excedencia, {', '.join(map(str, res))} juntos", fontsize=10)
    a2.grid(alpha=0.3, lw=0.5); a2.legend(frameon=False, fontsize=9)
    fig.suptitle(f"{nombre}: WRF-SAAG vs ERA5, FMA", fontsize=12)
    fig.tight_layout(); fig.savefig(FIGURAS / "era5_comparacion_dispersion.png", dpi=150); plt.close(fig)

    # mapas del acumulado FMA
    n = len(res)
    fig, axs = plt.subplots(n, 4, figsize=(17, 4.3 * n), squeeze=False)
    tots = {}
    for a, r in res.items():
        sg, er = r["sg"], r["er"]
        ts = sg.pr.sum("time", min_count=1).values
        te = er.pr.sum("time", min_count=1).values
        tse = saag_en_malla_era5(ts, sg.XLAT.values, sg.XLONG.values, er.lat.values, er.lon.values)
        tots[a] = (ts, tse, te)
    vmax = np.nanpercentile(np.concatenate([np.concatenate([t[0][mask], t[2].ravel(), t[1].ravel()]) for t in tots.values()]), 99)
    dmax = np.nanmax([np.nanmax(np.abs(t[1] - t[2])) for t in tots.values()])
    LO, LA = np.meshgrid(next(iter(res.values()))["er"].lon.values, next(iter(res.values()))["er"].lat.values)
    for i, (a, (ts, tse, te)) in enumerate(tots.items()):
        sg = res[a]["sg"]
        paneles = [(sg.XLONG.values, sg.XLAT.values, np.ma.masked_where(~mask, ts), "SAAG 4 km", "RdPu", 0, vmax),
                   (LO, LA, np.ma.masked_invalid(tse), "SAAG en malla ERA5", "RdPu", 0, vmax),
                   (LO, LA, np.ma.masked_invalid(te), "ERA5 0.25°", "RdPu", 0, vmax),
                   (LO, LA, np.ma.masked_invalid(tse - te), "SAAG − ERA5", "BrBG", -dmax, dmax)]
        for j, (X, Y, Z, tit, cm, v0, v1) in enumerate(paneles):
            ax = axs[i, j]
            h = ax.pcolormesh(X, Y, Z, cmap=cm, vmin=v0, vmax=v1, shading="nearest")
            mapas.dibujar_contorno(ax, geom)
            ax.set_title(f"{tit} — {a}", fontsize=10); ax.set_aspect("equal")
            if j == 2:
                h_tot = h
            if j == 3:
                h_dif = h
    fig.colorbar(h_tot, ax=axs[:, :3].ravel().tolist(), orientation="horizontal", fraction=0.04, pad=0.06,
                 shrink=0.6, label="Acumulado FMA (mm)")
    fig.colorbar(h_dif, ax=axs[:, 3].tolist(), orientation="horizontal", fraction=0.04, pad=0.06,
                 label="Diferencia (mm)")
    fig.suptitle(f"Acumulado FMA — {nombre}: WRF-SAAG vs ERA5", fontsize=13, y=0.93)
    fig.savefig(FIGURAS / "era5_comparacion_mapas.png", dpi=130, bbox_inches="tight"); plt.close(fig)
    print("figuras: era5_comparacion_serie.png, era5_comparacion_mensual.png, "
          "era5_comparacion_dispersion.png, era5_comparacion_mapas.png")


if __name__ == "__main__":
    main()
