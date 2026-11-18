"""WRF-SAAG frente a estaciones (Genaro Herrera, Bagazán) y PISCO v3, FMA 2005-2010-2015.

Uso:
    python scripts/10_estaciones.py

Entrada:
    figures/estaciones_obs_pisco3_diaria_FMA.csv   lluvia diaria observada (ANDREA, ANA-SENAMHI) y de PISCO v3
                                                   en la celda de cada estación (preparado por el grupo)
    data/processed/saag_pr_diaria_FMA_<año>.nc     SAAG diario (01_extraer_saag.py)

WRF-SAAG se toma en la celda de 4 km más cercana a cada estación; el rango de las 9 celdas vecinas
(~12 x 12 km) se muestra como barra. Mismo día pluviométrico (07-07 hora local) en las tres fuentes.

Escribe en figures/:
    estaciones_diaria.csv           día a día: observado, PISCO v3 y SAAG (celda) por estación
    estaciones_resumen.csv          por estación y año: totales FMA, diferencia vs observado, días con
                                    lluvia, correlación diaria y semanal, percentil 95 y máximo
    estaciones_precip_mensual.png   lluvia mensual observado / PISCO v3 / WRF-SAAG
    estaciones_dias_lluvia.png      días con lluvia (>= 1 mm) por mes
"""
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import PROCESSED, FIGURAS, PERIODO, ANIOS, MESES

ESTACIONES = {"genaro_herrera": ("Genaro Herrera", -4.905706, -73.649722),
              "bagazan": ("Bagazán", -4.909633, -73.603767)}
UMBRAL = 1.0
NOM_MES = {2: "Feb", 3: "Mar", 4: "Abr"}
COL = {"obs": "#2b2b2b", "pisco": "#1f77b4", "saag": "#d95f02"}


def cargar():
    d = pd.read_csv(FIGURAS / "estaciones_obs_pisco3_diaria_FMA.csv", parse_dates=["Fecha"]).set_index("Fecha")
    d = d.rename(columns={"Año": "anio", "Mes": "mes"})
    for a in ANIOS:
        s = xr.open_dataset(PROCESSED / f"saag_pr_diaria_{PERIODO}_{a}.nc")
        sel = d.anio == a
        assert sel.sum() == s.sizes["time"], f"{a}: el CSV y SAAG no tienen los mismos días"
        for k, (_, la, lo) in ESTACIONES.items():
            dist = np.hypot(s.XLAT.values - la, (s.XLONG.values - lo) * np.cos(np.radians(la)))
            j, i = np.unravel_index(dist.argmin(), dist.shape)
            d.loc[sel, f"saag_{k}_mm"] = s.pr[:, j, i].values
            for dj in (-1, 0, 1):
                for di in (-1, 0, 1):
                    d.loc[sel, f"_v_{k}_{dj}_{di}"] = s.pr[:, j + dj, i + di].values
            if a == ANIOS[0]:
                print(f"{ESTACIONES[k][0]}: celda SAAG a {dist.min() * 111:.1f} km")
    return d


def resumen(d):
    filas = []
    sem = lambda x: x.rolling(7, center=True).mean().dropna()
    for k, (nom, _, _) in ESTACIONES.items():
        for a, g in d.groupby("anio"):
            o = g[f"obs_{k}_mm"]
            f = dict(estacion=nom, anio=a, obs_FMA_mm=o.sum(), dias_lluvia_obs=int((o >= UMBRAL).sum()),
                     p95_obs=np.percentile(o[o >= UMBRAL], 95), max_obs=o.max())
            for c in ("pisco", "saag"):
                x = g[f"{c}_{k}_mm"]
                f.update({f"{c}_FMA_mm": x.sum(), f"{c}_dif_vs_obs_pct": 100 * (x.sum() / o.sum() - 1),
                          f"dias_lluvia_{c}": int((x >= UMBRAL).sum()), f"r_diaria_{c}": np.corrcoef(o, x)[0, 1],
                          f"r_7dias_{c}": np.corrcoef(sem(o), sem(x))[0, 1],
                          f"p95_{c}": np.percentile(x[x >= UMBRAL], 95), f"max_{c}": x.max()})
            filas.append(f)
    return pd.DataFrame(filas).round(2)


def figura(d, tipo, archivo):
    agg = (lambda x: x.sum()) if tipo == "mm" else (lambda x: (x >= UMBRAL).sum())
    fig, axs = plt.subplots(2, len(ANIOS), figsize=(16, 9), sharey=True, squeeze=False)
    for r, (k, (nom, _, _)) in enumerate(ESTACIONES.items()):
        vec = [c for c in d.columns if c.startswith(f"_v_{k}_")]
        for c, a in enumerate(ANIOS):
            ax, g, x, w = axs[r, c], d[d.anio == a], np.arange(len(MESES)), 0.27
            val = {s: [agg(g[g.mes == m][f"{s}_{k}_mm"]) for m in MESES] for s in ("obs", "pisco", "saag")}
            vv = np.array([[agg(g[g.mes == m][v]) for v in vec] for m in MESES])
            dy = 8 if tipo == "mm" else 0.4
            for off, s, lab in ((-w, "obs", "Observado"), (0, "pisco", "PISCO v3"), (w, "saag", "WRF-SAAG (celda de la estación)")):
                ax.bar(x + off, val[s], w, color=COL[s], label=lab)
                tope = vv.max(1) if s == "saag" else np.array(val[s])
                for xi, v, t in zip(x + off, val[s], tope):
                    ax.text(xi, max(v, t) + dy, f"{v:.0f}", ha="center", fontsize=8.5,
                            color="#7a3a00" if s == "saag" else "0.15")
            sv = np.array(val["saag"])
            ax.errorbar(x + w, sv, yerr=[sv - vv.min(1), vv.max(1) - sv], fmt="none", ecolor="#7a3a00", capsize=3, lw=1)
            ax.set_xticks(x, [NOM_MES[m] for m in MESES]); ax.set_title(f"{nom} – {a}", fontsize=11)
            ax.grid(axis="y", alpha=0.3, lw=0.5); ax.spines[["top", "right"]].set_visible(False)
            if c == 0:
                ax.set_ylabel("Precipitación mensual (mm)" if tipo == "mm" else "Días de lluvia (≥ 1 mm)")
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.95), fontsize=11)
    fig.suptitle("Precipitación mensual: Observado vs PISCO v3 vs WRF-SAAG" if tipo == "mm"
                 else "Días de lluvia por mes: Observado vs PISCO v3 vs WRF-SAAG", fontsize=14, y=0.995)
    fig.text(0.5, 0.01, "WRF-SAAG: celda de 4 km más cercana a cada estación; barra = rango de las 9 celdas vecinas "
             "(≈12 × 12 km). PISCO v3: celda de 0.1° de la estación (la misma para ambas). Día de lluvia: ≥ 1 mm.",
             ha="center", fontsize=8.5, color="0.35")
    fig.tight_layout(rect=(0, 0.03, 1, 0.93)); fig.savefig(FIGURAS / archivo, dpi=200); plt.close(fig)
    print(f"  {archivo}")


def main():
    d = cargar()
    cols = ["anio", "mes"] + [f"{s}_{k}_mm" for k in ESTACIONES for s in ("obs", "pisco", "saag")]
    out = d[cols].round(2); out.index = out.index.strftime("%Y-%m-%d"); out.index.name = "fecha"
    out.to_csv(FIGURAS / "estaciones_diaria.csv")
    t = resumen(d); t.to_csv(FIGURAS / "estaciones_resumen.csv", index=False)
    print(t.T.to_string())
    figura(d, "mm", "estaciones_precip_mensual.png")
    figura(d, "dias", "estaciones_dias_lluvia.png")


if __name__ == "__main__":
    main()
