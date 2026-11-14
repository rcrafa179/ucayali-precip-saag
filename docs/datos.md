# Descarga de datos

Dominio común: **5.3°S–4.4°S, 74.0°W–73.1°W** (Ucayali bajo, entre Requena y Nauta; ver `scripts/config.py`). Periodo: **FMA (1 feb – 30 abr) de 2005, 2010 y 2015**, en **valores diarios**.

## Día pluviométrico (importante)
Todos los productos se acumulan con la misma ventana, `DIA_INICIO_UTC` en `config.py`:
- **12 (por defecto):** el día D va de D 12:00 UTC a D+1 12:00 UTC, es decir de 07:00 a 07:00 hora local. Es la convención de las estaciones de SENAMHI, pensada para comparar con PISCO. Hay que verificar en la documentación de PISCO si la fecha corresponde al día en que empieza o en que termina la ventana; si corresponde al de término, hay que desplazar PISCO un día.
- **0:** día UTC (00 a 00), como IMERG diario.

Por eso para FMA se necesitan datos horarios **desde el 1 de febrero 12 UTC hasta el 1 de mayo 12 UTC**.

## WRF-SAAG (NCAR GDEX d616000)
- No requiere cuenta. Se lee por OPeNDAP solo la caja de la cuenca.
- Catálogo: https://tds.gdex.ucar.edu/thredds/catalog/files/g/d616000/catalog.html
- Archivos 2D horarios: `hist2D/<YYYYMM>/wrf2d_d01_YYYY-MM-DD_HHMMSS.nc` (~700 MB c/u, todo el continente).
- OPeNDAP de un archivo: `https://tds.gdex.ucar.edu/thredds/dodsC/files/g/d616000/hist2D/201501/wrf2d_d01_2015-01-10_120000.nc`
- Constantes (XLAT, XLONG, HGT): `INVARIANT/wrfconstants_SAAG.nc`. HGT no viene en los archivos 2D.
- **Precipitación: `PREC_ACC_NC` [mm], acumulada cada 60 min (`PREC_ACC_DT = 60`)**, así que ya es horaria. El valor a las HH:00 UTC es la lluvia entre HH−1 y HH.
- Sin parametrización de cúmulos (`CU_PHYSICS = 0`): `PREC_ACC_NC` es la precipitación total. `SNOW_ACC_NC` y `GRAUPEL_ACC_NC` son fracciones de esa misma precipitación.
- Configuración del modelo (atributos del archivo): WRF V4.1.5, dx = 4 km, Lambert (TRUELAT −5/−40, STAND_LON −58), microfísica Thompson (8), PBL YSU (1), radiación RRTMG (4), superficie Noah-MP (4), dt = 20 s.
- Malla 1471 × 2027, fila 0 = extremo sur. Dominio: `y[1439:1467]`, `x[292:319]` (28 × 27 puntos de 4 km).
- Si cambian la caja en `config.py`, el script recalcula sola la malla (`malla_ucayali.nc`).
- Variables útiles para el análisis: `REFL_COM` (reflectividad compuesta), `AFWA_CAPE_MU`, `AFWA_PWAT`, `OLR` (para comparar con satélite) y `W_UP_MAX`.
- El SAAG **no tiene salida diaria**: el script lee las 24 horas de cada día (solo `PREC_ACC_NC`, solo la caja) y las suma. FMA son 89 días = 2136 horas por año.
- Script: `python scripts/01_extraer_saag.py prueba` (un día), luego `... 2005`, etc.
- Salida: `data/raw/saag/<año>/saag_pr_diaria_<YYYYMM>.nc` (checkpoint mensual) y `data/processed/saag_pr_diaria_FMA_<año>.nc`. Variables `pr` [mm/día] y `n_horas` (24 = día completo).

## ERA5 (Copernicus CDS)
1. Cuenta en https://cds.climate.copernicus.eu y aceptar la licencia de *ERA5 hourly data on single levels*.
2. Token en `~/.cdsapirc` (nunca subirlo al repo).
3. `python scripts/02_descargar_era5.py 2005 2010 2015` → descarga feb, mar, abr y el 1 de mayo (horario).
4. `python scripts/03_diario_obs.py era5 2005 2010 2015` → `data/processed/era5_pr_diaria_FMA_<año>.nc`.
- `tp` viene en **metros** (×1000 → mm). El valor a la hora H es lo acumulado entre H−1 y H (UTC), igual que el SAAG.

## GPM IMERG V07 (NASA GES DISC)
1. Cuenta en https://urs.earthdata.nasa.gov y autorizar la app **NASA GESDISC DATA ARCHIVE**.
2. En https://disc.gsfc.nasa.gov buscar **GPM_3IMERGHH**, abrir **Subset / Get Data** y configurar:
   - fechas: **del 1 de febrero 12:00 UTC al 1 de mayo 12:00 UTC** de cada año;
   - caja: el dominio común (N −4.4, S −5.3, O −74.0, E −73.1);
   - variable: `precipitation`;
   - formato: netCDF.
3. Descargar la lista de enlaces y bajarla con:
   ```bash
   wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies \
        --auth-no-challenge=on --user=USUARIO --ask-password -c -i lista_2005.txt -P data/raw/imerg/2005
   ```
4. `python scripts/03_diario_obs.py imerg 2005 2010 2015` → `data/processed/imerg_pr_diaria_FMA_<año>.nc`.
- Unidades en mm/h con paso de 30 min (la fecha marca el **inicio** del intervalo). El script multiplica por 0.5 h y suma los 48 pasos del día.
- Alternativa más liviana: GPM_3IMERGDF (diario), pero su día es UTC (00–00) y no coincide con la ventana de 12 UTC.

## PISCO-prec (SENAMHI)
- NetCDF diario para todo el Perú (1981–2016). Repositorio de SENAMHI o IRI Data Library. Sin cuenta.
- Guardar en `data/raw/pisco/`. Es la **referencia principal** a escala diaria; sirve también para la climatología FMA.
- Revisar la convención de fecha (ver *Día pluviométrico* arriba).

## Límite de la cuenca
- ANA (unidades hidrográficas) o HydroBASINS. Guardar en `data/aux/`.
