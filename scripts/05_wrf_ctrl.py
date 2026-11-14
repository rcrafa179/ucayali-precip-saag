"""Corridas WRF locales (WRF2d_CTRL_*.nc) -> mismo formato diario FMA que SAAG, más ciclo diurno y altura.

Los WRF2d_CTRL_<inicio>-<fin>_<n>.nc son recortes de la misma simulación WRF-SAAG (4 km, horario,
PREC_ACC_NC) sobre otro dominio (~15.6-7.7°S, 77.0-70.5°W: Ucayali alto y medio con los Andes).
Cada año viene en 3 archivos de 2920 h; se unen y se usa la misma definición de día pluviométrico.

Uso:
    python scripts/05_wrf_ctrl.py ~/Downloads              # 2005, 2010, 2015 (los que encuentre)
    python scripts/05_wrf_ctrl.py ~/Downloads 2015

Escribe:
    data/processed/wrfctrl_pr_diaria_FMA_<año>.nc      (pr, n_horas, HGT; igual que saag_pr_diaria_*)
    data/processed/wrfctrl_ciclo_diurno_FMA_<año>.nc   (lluvia media por hora UTC, mm/h)
    figures/wrfctrl_ciclo_diurno.png                   ciclo diurno (hora local) por banda de altura
    figures/wrfctrl_lluvia_vs_altura.png               lluvia FMA vs altura del terreno
    figures/wrfctrl_ciclo_diurno.csv, figures/wrfctrl_lluvia_por_altura.csv
Después: python scripts/04_mapas_mensuales.py --fuente wrfctrl
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import PROCESSED, FIGURAS, PERIODO, ANIOS, DIA_INICIO_UTC, UTC_OFFSET_H, dias, horas_del_dia

BANDAS = [(0, 500, "< 500 m (llano amazónico)"), (500, 1500, "500–1500 m (piedemonte)"),
          (1500, 3000, "1500–3000 m (vertiente andina)"), (3000, 9000, "> 3000 m (alto andino)")]
COLORES = ["#9ecae1", "#4292c6", "#08519c", "#08306b"]   # una sola gama: bandas ordenadas por altura


def abrir_anio(carpeta, anio, horas):
    fs = sorted(Path(carpeta).expanduser().glob(f"WRF2d_CTRL_{anio}*.nc"))
    if not fs:
        return None
    print(f"{anio}: {len(fs)} archivos")
    partes = [xr.open_dataset(f) for f in fs]
    trozos = [p[["PREC_ACC_NC"]].sel(Time=p.Time.isin(horas)) for p in partes]   # solo las horas de FMA
    trozos = [t for t in trozos if t.sizes["Time"]] or [partes[0][["PREC_ACC_NC"]].isel(Time=[])]
    ds = xr.concat(trozos, dim="Time")   # HGT/LANDMASK no dependen del tiempo
    ds["HGT"], ds["LANDMASK"] = partes[0]["HGT"], partes[0]["LANDMASK"]
    t = pd.DatetimeIndex(ds.Time.values)
    if t.duplicated().any():
        ds = ds.isel(Time=~t.duplicated())
    return ds


def procesar(carpeta, anio):
    fechas = dias(anio)
    horas = pd.DatetimeIndex(np.concatenate([horas_del_dia(d) for d in fechas]))
    ds = abrir_anio(carpeta, anio, horas)
    if ds is None:
        print(f"{anio}: no hay WRF2d_CTRL_{anio}*.nc en {carpeta}, salto")
        return None
    pr = ds.PREC_ACC_NC.reindex(Time=horas).values.astype("float32")          # faltantes -> NaN
    ny, nx = pr.shape[1:]
    pr_h = pr.reshape(len(fechas), 24, ny, nx)
    n_horas = np.isfinite(pr_h).all(axis=(2, 3)).sum(axis=1).astype("int8")
    diaria = np.nansum(pr_h, axis=1)
    diaria[n_horas == 0] = np.nan
    coords = {"XLAT": (("south_north", "west_east"), ds.XLAT.values),
              "XLONG": (("south_north", "west_east"), ds.XLONG.values)}
    out = xr.Dataset(
        {"pr": (("time", "south_north", "west_east"), diaria, {"units": "mm/día"}),
         "n_horas": (("time",), n_horas),
         "HGT": (("south_north", "west_east"), ds.HGT.values, {"units": "m"}),
         "LANDMASK": (("south_north", "west_east"), ds.LANDMASK.values)},
        coords={"time": fechas, **coords},
        attrs={"fuente": "WRF2d_CTRL (recorte local de WRF-SAAG 4 km)",
               "dia_pluviometrico": f"día D = [D {DIA_INICIO_UTC:02d} UTC, D+1 {DIA_INICIO_UTC:02d} UTC)"})
    PROCESSED.mkdir(parents=True, exist_ok=True)
    f = PROCESSED / f"wrfctrl_pr_diaria_{PERIODO}_{anio}.nc"
    out.to_netcdf(f, encoding={"pr": {"zlib": True, "complevel": 4}})
    print(f"  {f.name}: {len(fechas)} días, incompletos {int((n_horas < 24).sum())}")

    hora_utc = (horas - pd.Timedelta(minutes=30)).hour          # hora de inicio del intervalo
    ciclo = np.stack([np.nanmean(pr[hora_utc == h], axis=0) for h in range(24)])
    cd = xr.Dataset({"pr": (("hora_utc", "south_north", "west_east"), ciclo, {"units": "mm/h"})},
                    coords={"hora_utc": np.arange(24), **coords},
                    attrs={"nota": "hora_utc = inicio del intervalo de 1 h (lluvia entre h y h+1 UTC)"})
    cd.to_netcdf(PROCESSED / f"wrfctrl_ciclo_diurno_{PERIODO}_{anio}.nc")
    return out, ciclo


def figuras(res):
    hgt = next(iter(res.values()))[0].HGT.values
    tierra = next(iter(res.values()))[0].LANDMASK.values > 0.5
    anios = list(res)
    # ciclo diurno por banda de altura, promedio de los años
    ciclo = np.mean([c for _, c in res.values()], axis=0)
    hl = (np.arange(24) + UTC_OFFSET_H) % 24
    orden = np.argsort(hl)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    filas, filas2 = [], []
    for (lo, hi, nom), col in zip(BANDAS, COLORES):
        m = tierra & (hgt >= lo) & (hgt < hi)
        if m.sum() == 0:
            continue
        serie = ciclo[:, m].mean(axis=1)
        ax.plot(hl[orden] + 0.5, serie[orden], color=col, lw=2, marker="o", ms=4, label=f"{nom}  ({m.sum()} celdas)")
        filas.append(dict(banda=nom, celdas=int(m.sum()), hora_local_max=int(hl[np.argmax(serie)]),
                          mm_h_max=serie.max(), mm_h_min=serie.min()))
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3))
    ax.set_xlabel(f"Hora local (UTC{UTC_OFFSET_H:+d})"); ax.set_ylabel("Lluvia media (mm/h)")
    ax.grid(alpha=0.3, lw=0.5); ax.legend(fontsize=8, frameon=False)
    ax.set_title(f"Ciclo diurno de la precipitación, FMA — WRF-SAAG 4 km\npromedio {', '.join(map(str, anios))}", fontsize=11)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / "wrfctrl_ciclo_diurno.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("  wrfctrl_ciclo_diurno.png")

    # lluvia FMA vs altura (medianas por tramos de 250 m)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    tramos = np.arange(0, hgt[tierra].max() + 250, 250)
    for (a, (ds, _)), col in zip(res.items(), ["#4292c6", "#e6550d", "#31a354"]):
        tot = ds.pr.where(ds.n_horas == 24).sum("time").values
        x, y = hgt[tierra], tot[tierra]
        k = np.digitize(x, tramos)
        cen = [(tramos[i - 1] + 125, np.median(y[k == i])) for i in np.unique(k) if (k == i).sum() >= 20]
        ax.plot(*zip(*cen), color=col, lw=2, label=str(a))
        for lo, hi, nom in BANDAS:
            m = (x >= lo) & (x < hi)
            if m.sum():
                filas2.append(dict(banda=nom, anio=a, total_FMA_mm_mediana=np.median(y[m]), total_FMA_mm_media=y[m].mean()))
    ax.set_xlabel("Altura del terreno (m)"); ax.set_ylabel("Lluvia acumulada FMA (mm), mediana por tramo de 250 m")
    ax.grid(alpha=0.3, lw=0.5); ax.legend(frameon=False)
    ax.set_title("Precipitación FMA vs altura — WRF-SAAG 4 km", fontsize=11)
    fig.savefig(FIGURAS / "wrfctrl_lluvia_vs_altura.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("  wrfctrl_lluvia_vs_altura.png")
    for nombre, f in (("wrfctrl_ciclo_diurno.csv", filas), ("wrfctrl_lluvia_por_altura.csv", filas2)):
        t = pd.DataFrame(f).round(2)
        t.to_csv(FIGURAS / nombre, index=False)
        print(f"\n{nombre}\n{t.to_string(index=False)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    carpeta, anios = sys.argv[1], [int(x) for x in sys.argv[2:]] or ANIOS
    res = {a: r for a in anios if (r := procesar(carpeta, a)) is not None}
    if res:
        figuras(res)
