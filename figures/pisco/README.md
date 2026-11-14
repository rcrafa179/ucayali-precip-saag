# Figuras de PISCO (referencia observacional)

Imágenes de precipitación de **PISCO-prec (SENAMHI)** sobre la Intercuenca 49911, para comparar con WRF-SAAG.

## Nombres de archivo

Usar siempre `pisco_<qué>_<período>.png`, por ejemplo:

| Archivo | Contenido |
|---|---|
| `pisco_climatologia_mensual_1981-2005.jpg` | climatología de los 12 meses, 1981–2005 |
| `pisco_total_FMA_2005.png` | acumulado mensual feb–mar–abr de 2005 |
| `pisco_total_FMA_2010.png` | ídem 2010 |
| `pisco_total_FMA_2015.png` | ídem 2015 |

El período va en el nombre para no confundir una climatología de décadas con los años del proyecto.

## Subirlas

```bash
git pull
# copiar las imágenes a figures/pisco/ con los nombres de arriba
git add figures/pisco/*.png figures/pisco/*.jpg
git commit -m "PISCO: figuras de la Intercuenca 49911"
git pull --rebase
git push
```

Agregar abajo, en la tabla, qué es cada imagen.

## Inventario

| Archivo | Período | Variable / unidades | Versión de PISCO | Autor |
|---|---|---|---|---|
| `pisco_climatologia_mensual_1981-2005.jpg` | 1981–2005 (promedio de cada mes) | precipitación, mm/mes | PISCOp v2.1 | AllSJ-23 |

Los mapas de PISCO para **FMA de 2005, 2010 y 2015** (los años del proyecto) se generan con los scripts y están en `figures/` con prefijo `pisco_` (ver la sección 5 del README principal). Esta carpeta es para figuras hechas aparte.
