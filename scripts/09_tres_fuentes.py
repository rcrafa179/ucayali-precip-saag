"""SAAG y ERA5 frente a PISCO en la misma tabla (pregunta 4: ¿la convección explícita a 4 km mejora a ERA5?).

Uso (después de 03_diario_obs.py era5 y pisco):
    python scripts/09_tres_fuentes.py

Escribe figures/tres_fuentes_resumen.csv: por año y fuente, total FMA de la cuenca, diferencia con PISCO (%),
correlación diaria y semanal con PISCO, días con lluvia (>= 1 mm), días > 20 mm y percentil 95.
Escribe figures/tres_fuentes_diaria.csv: lluvia diaria media de la cuenca (mm) de las tres fuentes, día por día.
"""
import numpy as np
import pandas as pd
import importlib.util as u
from pathlib import Path

from config import ANIOS, FIGURAS

s = u.spec_from_file_location("c", Path(__file__).with_name("08_comparar.py"))
c = u.module_from_spec(s); s.loader.exec_module(c)


def serie_ref(ref, anio, geom):
    c.REF = ref
    e = c.cargar_ref(anio)
    if e is None:
        return None
    w = c.pesos_era5(e.lat.values, e.lon.values, geom)
    p = e.pr.values; ok = np.isfinite(p)
    return pd.Series(np.nansum(np.where(ok, p, 0) * w, axis=(1, 2)) / (ok * w).sum(axis=(1, 2)),
                     index=pd.DatetimeIndex(e.time.values))


def main():
    geom, nombre = c.mapas.cargar_cuenca(None)
    filas, diarias = [], []
    for a in ANIOS:
        sg = c.mapas.cargar(a)
        E, P = serie_ref("era5", a, geom), serie_ref("pisco", a, geom)
        if sg is None or E is None or P is None:
            print(f"{a}: falta SAAG, ERA5 o PISCO, salto"); continue
        m = c.mapas.mascara_celdas(sg, geom)
        S = pd.Series(np.nanmean(sg.pr.values[:, m], axis=1), index=pd.DatetimeIndex(sg.time.values))
        sem = lambda x: x.rolling(7, center=True).mean().dropna()
        diarias.append(pd.DataFrame({"anio": a, "saag_mm": S, "era5_mm": E, "pisco_mm": P}))
        for nom, X in (("SAAG", S), ("ERA5", E), ("PISCO", P)):
            f = dict(anio=a, fuente=nom, total_FMA_mm=X.sum(), dias_lluvia=int((X >= 1).sum()),
                     dias_20mm=int((X >= 20).sum()), p95_mm=np.percentile(X, 95))
            if nom != "PISCO":
                f.update(dif_vs_pisco_pct=100 * (X.sum() / P.sum() - 1), r_diaria=np.corrcoef(X, P)[0, 1],
                         r_7dias=np.corrcoef(sem(X), sem(P))[0, 1])
            filas.append(f)
    d = pd.concat(diarias).round(2)
    d.index = d.index.strftime("%Y-%m-%d"); d.index.name = "fecha"
    d.to_csv(FIGURAS / "tres_fuentes_diaria.csv")
    print(f"tres_fuentes_diaria.csv: {len(d)} días")
    t = pd.DataFrame(filas).round(2)
    t.to_csv(FIGURAS / "tres_fuentes_resumen.csv", index=False)
    print(t.to_string(index=False))
    m = t[t.fuente != "PISCO"].assign(abs_dif=lambda d: d.dif_vs_pisco_pct.abs())
    print("\nPromedio de los años (frente a PISCO):")
    print(m.groupby("fuente")[["abs_dif", "r_diaria", "r_7dias"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
