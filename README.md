# Evaluación de la precipitación diaria simulada con WRF a escala convectiva (4 km) en la cuenca del Ucayali: febrero–abril de 2005, 2010 y 2015

Proyecto del **Taller de Hidroclima y simulaciones de convección explícita en Sudamérica tropical**.

## Objetivo

Caracterizar y evaluar la **precipitación diaria acumulada** de la simulación **WRF-SAAG (NCAR, 4 km, convección explícita)** en la cuenca del Ucayali durante **FMA (febrero–abril)** de 2005, 2010 y 2015, comparándola con PISCO, IMERG y ERA5.

FMA es el final de la estación lluviosa. 2005 y 2010 fueron años de sequía amazónica y 2015 de El Niño.

Preguntas guía:
1. ¿Qué tan bien reproduce el WRF a 4 km el acumulado de FMA y su distribución espacial?
2. ¿Representa bien la frecuencia de días lluviosos y la intensidad diaria, incluidos los extremos?
3. ¿Dónde falla más, en la vertiente andina o en el llano amazónico?
4. ¿Mejora respecto a ERA5, que es su forzante?
5. ¿Distingue las diferencias entre 2005, 2010 y 2015?

## Datos

| Base | Uso | Resolución | Acceso |
|---|---|---|---|
| **WRF-SAAG** (GDEX d616000) | Modelo evaluado | 4 km, horaria → diaria | OPeNDAP, sin cuenta |
| **PISCO-prec** (SENAMHI) | Referencia principal (Andes peruanos) | 0.1°, diaria | Libre |
| **GPM IMERG V07** (GPM_3IMERGHH) | Referencia satelital | 0.1°, 30 min → diaria | NASA Earthdata |
| **ERA5** | Forzante / contraste | 0.25°, horaria → diaria | Copernicus CDS |

**Día pluviométrico:** todos los productos se acumulan con la misma ventana, definida en `scripts/config.py` (`DIA_INICIO_UTC`). Por defecto es 12 UTC (07:00 a 07:00 hora local), la convención de las estaciones de SENAMHI, para comparar con PISCO.

Instrucciones de descarga: [`docs/datos.md`](docs/datos.md).

## Estructura

```
scripts/        código reutilizable (config.py = caja, años, rutas)
notebooks/      análisis exploratorio y figuras
data/raw/       datos descargados (NO se suben a git)
data/processed/ datos homogeneizados (NO se suben a git)
data/aux/       shapefile de la cuenca, DEM
figures/        figuras finales
docs/           plan de trabajo y notas
```

## Instalación

```bash
conda env create -f environment.yml      # crea el entorno "ucayali"
conda activate ucayali
```

Si usan el entorno del curso (`taller-rhia`), solo hay que agregar:
```bash
conda activate taller-rhia
mamba install -c conda-forge xesmf regionmask
```

## Flujo de trabajo

Todos los comandos se corren **desde la raíz del repo**.

```bash
python scripts/01_extraer_saag.py prueba          # verifica acceso y mide velocidad con un día
python scripts/01_extraer_saag.py 2005            # FMA 2005 diario (reanudable por mes)
python scripts/02_descargar_era5.py 2005          # ERA5 horario de FMA
python scripts/03_diario_obs.py era5 2005         # ERA5 a diario
python scripts/03_diario_obs.py imerg 2005        # IMERG a diario
```

**Mapas mensuales:** `python scripts/04_mapas_mensuales.py` lee `data/processed/saag_pr_diaria_FMA_<año>.nc` y guarda en `figures/` la climatología mensual (promedio de los años disponibles), el acumulado y los días con lluvia de cada año y un CSV de resumen. Por defecto usa `cuenca/49911.shp` (Intercuenca 49911, ANA, 4353 km², incluida en el repo); con `--shp otra.shp` usa otra cuenca. Muestra solo las celdas de 4 km que tocan la cuenca y dibuja su contorno; sin cuenca muestra todo el dominio. Los días con horas faltantes se excluyen de los acumulados.

Mientras corre, `01_extraer_saag.py` imprime cada minuto una línea de estado con el avance del año, la velocidad de los últimos 5 min, los reintentos, las horas fallidas y el tiempo restante. Si los reintentos suben o la velocidad cae, NCAR está limitando: bajen `--workers`.

Salidas diarias en `data/processed/`: `saag_pr_diaria_FMA_<año>.nc`, `era5_...`, `imerg_...`.
Cada archivo incluye un contador de pasos válidos por día (`n_horas` / `n_pasos`) para detectar días incompletos.


Plan completo y reparto de tareas: [`docs/plan.md`](docs/plan.md).

## Reglas del grupo

- **No subir datos** (`*.nc`, `*.zarr`, `*.HDF5`): ya están en `.gitignore`. Cada uno descarga los suyos.
- **No subir credenciales** (`.cdsapirc`, `.netrc`).
- Cada tarea en su propia rama: `git checkout -b nombre/tarea`. Se integra a `main` con Pull Request.
- Antes de hacer commit de un notebook, limpien las salidas pesadas o usen `nbstripout`.
- Los parámetros comunes (caja, años, meses, día pluviométrico, rutas) solo se cambian en `scripts/config.py`.
- Tiempo: los datos crudos están en **UTC**. La fecha de cada día diario es la del inicio de la ventana.

## Cita del dataset principal

Rasmussen, R., Liu, C., Ikeda, K., Dominguez, F. (2022). *Multi-decadal Convection-permitting Simulation of Current Climate over South America using WRF*. NSF NCAR. https://doi.org/10.5065/6XQW-ZB02
