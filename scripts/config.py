"""Configuración común del proyecto. Cambiar aquí, no en cada script."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Años del proyecto
ANIOS = [2005, 2010, 2015]

# Caja del Ucayali con margen (grados)
LAT_MIN, LAT_MAX = -15.8, -3.2
LON_MIN, LON_MAX = -77.8, -69.8
AREA_CDS = [LAT_MAX, LON_MIN, LAT_MIN, LON_MAX]  # N, O, S, E (formato Copernicus)

# Zona horaria local (Perú)
UTC_OFFSET_H = -5

# Carpetas de datos (ignoradas por git)
DATA = RAIZ / "data"
RAW_SAAG = DATA / "raw" / "saag"
RAW_ERA5 = DATA / "raw" / "era5"
RAW_IMERG = DATA / "raw" / "imerg"
RAW_PISCO = DATA / "raw" / "pisco"
PROCESSED = DATA / "processed"
AUX = DATA / "aux"          # shapefile de la cuenca, DEM, etc.
FIGURAS = RAIZ / "figures"
