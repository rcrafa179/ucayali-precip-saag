"""Configuración común del proyecto. Cambiar aquí, no en cada script."""
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

# ---------------- Alcance ----------------
ANIOS = [2005, 2010, 2015]
MESES = [2, 3, 4]            # FMA: febrero, marzo, abril
PERIODO = "FMA"

# Dominio de trabajo (grados): Ucayali bajo, entre Requena y la confluencia con el Marañón (Nauta)
LAT_MIN, LAT_MAX = -5.3, -4.4
LON_MIN, LON_MAX = -74.0, -73.0
AREA_CDS = [LAT_MAX, LON_MIN, LAT_MIN, LON_MAX]  # N, O, S, E (formato Copernicus)

# ---------------- Día pluviométrico ----------------
# Un "día D" acumula la lluvia de [D + DIA_INICIO_UTC, D+1 + DIA_INICIO_UTC) en UTC.
#   12 -> 07:00 a 07:00 hora local (UTC-5), la convención de las estaciones de SENAMHI
#         usada para comparar con PISCO.  Verificar cómo PISCO etiqueta la fecha.
#    0 -> día UTC (00 a 00), como IMERG diario (GPM_3IMERGDF).
# Debe ser el MISMO para SAAG, IMERG y ERA5.
DIA_INICIO_UTC = 12
UTC_OFFSET_H = -5  # Perú

# ---------------- Carpetas (ignoradas por git) ----------------
DATA = RAIZ / "data"
RAW_SAAG = DATA / "raw" / "saag"
RAW_ERA5 = DATA / "raw" / "era5"
RAW_IMERG = DATA / "raw" / "imerg"
RAW_PISCO = DATA / "raw" / "pisco"
PROCESSED = DATA / "processed"
AUX = DATA / "aux"          # shapefile de la cuenca, DEM, etc.
FIGURAS = RAIZ / "figures"


def dias(anio):
    """Fechas (etiqueta del día) del periodo FMA de un año."""
    ini = pd.Timestamp(anio, MESES[0], 1)
    fin = pd.Timestamp(anio, MESES[-1], 1) + pd.offsets.MonthEnd(0)
    return pd.date_range(ini, fin, freq="D")


def horas_del_dia(d):
    """Marcas horarias (UTC, fin de hora) cuya lluvia cae en el día pluviométrico d.
    Un valor horario con fecha HH:00 es la lluvia entre HH-1 y HH."""
    ini = pd.Timestamp(d) + pd.Timedelta(hours=DIA_INICIO_UTC)
    return pd.date_range(ini + pd.Timedelta(hours=1), periods=24, freq="h")
