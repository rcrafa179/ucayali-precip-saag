# Descarga de datos

Caja común: **3.2°S–15.8°S, 77.8°W–69.8°W** (ver `scripts/config.py`). Años: 2005, 2010 y 2015.

## WRF-SAAG (NCAR GDEX d616000)
- No requiere cuenta. Se lee por OPeNDAP solo la caja de la cuenca.
- Catálogo: https://tds.gdex.ucar.edu/thredds/catalog/files/g/d616000/catalog.html
- Archivos 2D horarios: `wrf2d_d01_YYYY-MM-DD_HHMMSS.nc` (~700 MB c/u, todo el continente).
- Constantes (XLAT, XLONG, HGT): `INVARIANT/wrfconstants_SAAG.nc`.
- Script: `python scripts/01_extraer_saag.py prueba`, luego `... 2005`, etc.
- Salida: `data/raw/saag/<año>/saag_prec_<YYYYMM>.nc`, en UTC.

## ERA5 (Copernicus CDS)
1. Cuenta en https://cds.climate.copernicus.eu y aceptar la licencia de *ERA5 hourly data on single levels*.
2. Token en `~/.cdsapirc` (nunca subirlo al repo).
3. `python scripts/02_descargar_era5.py 2005 2010 2015`
- `tp` viene en **metros** (×1000 → mm). El valor a la hora H es lo acumulado entre H−1 y H (UTC).

## GPM IMERG V07 (NASA GES DISC)
1. Cuenta en https://urs.earthdata.nasa.gov y autorizar la app **NASA GESDISC DATA ARCHIVE**.
2. En https://disc.gsfc.nasa.gov buscar **GPM_3IMERGHH**, abrir **Subset / Get Data** y configurar:
   - fechas: año completo;
   - caja: la caja común;
   - variable: `precipitation`;
   - formato: netCDF.
3. Descargar la lista de enlaces y bajarla con:
   ```bash
   wget --load-cookies ~/.urs_cookies --save-cookies ~/.urs_cookies --keep-session-cookies \
        --auth-no-challenge=on --user=USUARIO --ask-password -c -i lista_2005.txt -P data/raw/imerg/2005
   ```
- Unidades en mm/h, con paso de 30 min: hay que promediar los dos semi-horarios para obtener mm por hora.

## PISCO-prec (SENAMHI)
- NetCDF diario para todo el Perú. Repositorio de SENAMHI o IRI Data Library. Sin cuenta.
- Guardar en `data/raw/pisco/`.

## Límite de la cuenca
- ANA (unidades hidrográficas) o HydroBASINS. Guardar en `data/aux/`.
