# Evaluación de la precipitación horaria simulada con WRF a escala convectiva (4 km) en la cuenca del Ucayali: 2005, 2010 y 2015

Proyecto del **Taller de Hidroclima y simulaciones de convección explícita en Sudamérica tropical**.

## Objetivo

Caracterizar y evaluar la precipitación horaria de la simulación **WRF-SAAG (NCAR, 4 km, convección explícita)** en la cuenca del Ucayali para 2005 y 2010 (sequías amazónicas) y 2015 (El Niño), comparándola con IMERG, PISCO y ERA5.

Preguntas guía:
1. ¿Qué tan bien reproduce el WRF a 4 km el acumulado, la estacionalidad y el **ciclo diurno** de la lluvia?
2. ¿Dónde falla más, en la vertiente andina o en el llano amazónico?
3. ¿Mejora respecto a ERA5, que es su forzante?
4. ¿Captura las anomalías de 2005, 2010 y 2015?

## Datos

| Base | Uso | Resolución | Acceso |
|---|---|---|---|
| **WRF-SAAG** (GDEX d616000) | Modelo evaluado | 4 km, horaria | OPeNDAP, sin cuenta |
| **GPM IMERG V07** (GPM_3IMERGHH) | Referencia horaria | 0.1°, 30 min | NASA Earthdata |
| **PISCO-prec** (SENAMHI) | Referencia diaria en los Andes | 0.1°, diaria | Libre |
| **ERA5** | Forzante / contraste | 0.25°, horaria | Copernicus CDS |

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
python scripts/01_extraer_saag.py prueba     # verificar acceso y variable
python scripts/01_extraer_saag.py 2005       # extraer un año (reanudable)
python scripts/02_descargar_era5.py 2005
```

Plan completo y reparto de tareas: [`docs/plan.md`](docs/plan.md).

## Reglas del grupo

- **No subir datos** (`*.nc`, `*.zarr`, `*.HDF5`): ya están en `.gitignore`. Cada uno descarga los suyos.
- **No subir credenciales** (`.cdsapirc`, `.netrc`).
- Cada tarea en su propia rama: `git checkout -b nombre/tarea`. Se integra a `main` con Pull Request.
- Antes de hacer commit de un notebook, limpien las salidas pesadas o usen `nbstripout`.
- Los parámetros comunes (caja, años, rutas) solo se cambian en `scripts/config.py`.
- Tiempo: los datos crudos están en **UTC**. Para el ciclo diurno se convierte a hora local (UTC−5).

## Cita del dataset principal

Rasmussen, R., Liu, C., Ikeda, K., Dominguez, F. (2022). *Multi-decadal Convection-permitting Simulation of Current Climate over South America using WRF*. NSF NCAR. https://doi.org/10.5065/6XQW-ZB02
