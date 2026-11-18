# Evaluación de la precipitación diaria simulada con WRF a escala convectiva (4 km) en la cuenca del Ucayali: febrero–abril de 2005, 2010 y 2015

Proyecto del **Taller de Hidroclima y simulaciones de convección explícita en Sudamérica tropical**.

## Objetivo

Caracterizar y evaluar la **precipitación diaria acumulada** de la simulación **WRF-SAAG (NCAR, 4 km, convección explícita)** en el bajo Ucayali durante **FMA (febrero–abril)** de 2005, 2010 y 2015, comparándola con estaciones de SENAMHI, PISCO v3, PISCO v2.1 y ERA5.

FMA es el final de la estación lluviosa. 2005 y 2010 fueron años de sequía amazónica [12–15] y 2015 de El Niño [16, 17]. La simulación evaluada se describe en [1, 2] y las referencias observacionales en [7, 18, 19].

Preguntas guía:
1. ¿Qué tan bien reproduce el WRF a 4 km el acumulado de FMA y su distribución espacial?
2. ¿Representa bien la frecuencia de días lluviosos y la intensidad diaria, incluidos los extremos?
3. ¿Dónde falla más dentro de la cuenca?
4. ¿Mejora respecto a ERA5, que es su forzante?
5. ¿Distingue las diferencias entre 2005, 2010 y 2015?

## Dominio

| | |
|---|---|
| Caja | 5.3–4.4°S, 74.0–73.0°W (bajo Ucayali, entre Requena y Nauta) |
| Malla SAAG | 28 × 30 puntos de 4 km, índices `y[1439:1467] x[292:322]` |
| Cuenca | **Intercuenca 49911** (ANA, Bajo Ucayali, 4353 km²): `cuenca/49911.shp`, incluida en el repo |
| Relieve | llano amazónico, 90–180 m |

La caja se define en `scripts/config.py`. Los mapas y estadísticas usan solo las 330 celdas de 4 km que tocan la cuenca.

## Datos

| Base | Uso | Resolución | Acceso |
|---|---|---|---|
| **WRF-SAAG** (GDEX d616000) | Modelo evaluado | 4 km, horaria → diaria | OPeNDAP, sin cuenta |
| **Estaciones Genaro Herrera** (−4.906, −73.650) **y Bagazán** (−4.910, −73.604) | Observación puntual | Diaria | Plataforma ANDREA (ANA-SENAMHI) |
| **PISCO v3** (SENAMHI) | Referencia grillada en las estaciones | 0.1° (~10 km), diaria, 1981–2025 | SENAMHI |
| **PISCO v2.1** (SENAMHI) | Referencia grillada a escala de cuenca | 0.1°, diaria, 1981–2016 | IRI Data Library, sin cuenta |
| **GPM IMERG V07** (GPM_3IMERGHH) | Referencia satelital | 0.1°, 30 min → diaria | NASA Earthdata |
| **ERA5** | Forzante / contraste | 0.25°, horaria → diaria | Copernicus CDS |

**Día pluviométrico:** todos los productos se acumulan con la misma ventana, definida en `scripts/config.py` (`DIA_INICIO_UTC`). Por defecto es 12 UTC, es decir de 07:00 a 07:00 hora local, que es la convención de las estaciones de SENAMHI y permite comparar con PISCO. La fecha de cada día es la del inicio de la ventana.

Instrucciones de descarga: [`docs/datos.md`](docs/datos.md).

## Estado de los resultados

| Parte | Datos | Figuras | Tablas | Responsable |
|---|---|---|---|---|
| SAAG 2005 | ✅ | ✅ | ✅ | brunedu21 |
| SAAG 2010 | ✅ | ✅ | ✅ | giswllmp |
| SAAG 2015 | ✅ | ✅ | ✅ | rcrafa179 |
| Climatología y análisis SAAG (combinado) | — | ✅ | ✅ | rcrafa179 |
| PISCO climatología 1981–2005 (imagen) | — | ✅ `figures/pisco/` | — | AllSJ-23 |
| Estaciones y PISCO v3 | ✅ `estaciones_obs_pisco3_diaria_FMA.csv` | ✅ `estaciones_*.png` | ✅ | AllSJ-23, rcrafa179 |
| ERA5 (comparación) | ✅ | ✅ `era5_comparacion_*` | ✅ | rcrafa179 |
| PISCO v2.1 (comparación de cuenca) | ✅ | ✅ `pisco_comparacion_*` | ✅ | rcrafa179 |

Pendiente (opcional): IMERG como segunda referencia satelital y una climatología de 20 años con WRF-SAAG (2000–2021).

## Resultados

Los resultados completos, con figuras y tablas, están en **[docs/resultados.md](docs/resultados.md)**. En resumen:

- **Frente a las estaciones** Genaro Herrera y Bagazán, WRF-SAAG queda dentro de ±20 % del acumulado de FMA; PISCO v3 se acerca más (−8 a +8 %, salvo Bagazán 2015).
- **WRF-SAAG reproduce mejor que PISCO v3 cómo llueve:** 44–55 días con lluvia en FMA frente a 31–51 observados y 68–76 de PISCO, y extremos más parecidos a los observados.
- **Los mayores errores del modelo** están en febrero (sobrestimado) y marzo (subestimado) de 2010.
- **Limitaciones:** PISCO v3 sigue casi día a día a Bagazán, Bagazán tiene datos dudosos y son solo 2 estaciones y 3 años.

## Estructura

```
scripts/          código (config.py = caja, años, meses, rutas)
cuenca/           shapefile de la Intercuenca 49911 (sí se sube)
data/raw/         datos crudos descargados (NO se suben)
data/processed/   resultado diario FMA por año (sí se sube, < 1 MB por año)
data/aux/         otros insumos locales (DEM, etc.)
figures/          mapas y tablas de resultados (sí se suben)
notebooks/        análisis exploratorio
docs/             plan de trabajo y notas
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
Los mapas leen el shapefile sin geopandas, así que no les afecta el error de PROJ/pyogrio que aparece en algunos entornos.

## Scripts

Todos los comandos se corren **desde la raíz del repo**.

| Script | Qué hace |
|---|---|
| `01_extraer_saag.py` | Lee de NCAR solo la caja del dominio, hora por hora, y guarda la lluvia diaria FMA de un año |
| `02_descargar_era5.py` | Descarga ERA5 horario de FMA (guarda tu clave con `--clave`) |
| `02b_descargar_pisco.py` | Descarga PISCOp v2.1 diario de FMA (sin cuenta); PISCO v3 en las estaciones viene en el CSV de estaciones |
| `03_diario_obs.py` | Pasa ERA5, IMERG o PISCO a diario con el mismo día pluviométrico |
| `04_mapas_mensuales.py` | Mapas mensuales y CSV de resumen sobre la cuenca |
| `05_wrf_ctrl.py` | Corridas locales `WRF2d_CTRL_*.nc` de otro dominio (solo uso local, ver abajo) |
| `06_subir_anio.py` | Sube al repo los resultados de un año, siempre de la misma forma |
| `07_analisis.py` | Serie diaria (figura y **CSV diario**), anomalías, intensidad y extremos de todos los años; `--fuente pisco` para PISCO |
| `08_comparar.py` | Compara SAAG con ERA5 o PISCO sobre la cuenca: totales, sesgo, correlación, extremos, mapas y chequeo de fechas |
| `09_tres_fuentes.py` | SAAG y ERA5 frente a PISCO en una sola tabla (pregunta 4) y CSV diario con las tres fuentes |
| `10_estaciones.py` | WRF-SAAG en la celda de cada estación frente a lo observado y PISCO v3: tablas y figuras de la presentación |

### 1. Extraer SAAG

```bash
python scripts/01_extraer_saag.py prueba --workers 20    # verifica acceso y mide la velocidad con un día
python scripts/01_extraer_saag.py 2010 --workers 20      # FMA 2010 (2136 horas, ~1–2 h)
```

- Son 2136 lecturas por año, una por hora, porque SAAG no guarda acumulados de más de una hora.
- `--workers 20` funciona bien. Si aparecen muchos reintentos o la velocidad cae (por ejemplo, porque varios del grupo descargan a la vez), bajen a 12.
- Cada minuto imprime una línea de estado: avance, velocidad de los últimos 5 min, reintentos, horas fallidas y tiempo restante.
- Es reanudable: guarda un archivo por mes en `data/raw/saag/<año>/` y, si se corta, al relanzar salta los meses ya hechos.
- Al final debe decir **`89 días`** y **`incompletos: 0`**.

Salida: `data/processed/saag_pr_diaria_FMA_<año>.nc`, con `pr` (mm/día), `n_horas` (horas válidas por día) y `HGT`.

### 2. Mapas y tablas

```bash
python scripts/04_mapas_mensuales.py 2010          # solo los archivos de 2010
python scripts/04_mapas_mensuales.py --combinado   # climatología y CSV con todos los años (coordinación)
```

Por año:
- `figures/mapas_total_<año>.png`: acumulado mensual (mm/mes), un panel por mes.
- `figures/mapas_diaslluvia_<año>.png`: días con lluvia ≥ 1 mm.
- `figures/mapas_resumen_mensual_<año>.csv`: promedio, mínimo y máximo sobre la cuenca por mes.

Con `--combinado`:
- `figures/mapas_climatologia.png`: promedio de los años, por mes.
- `figures/mapas_resumen_mensual_todos.csv`: las tablas de todos los años juntas.

Por defecto usa `cuenca/49911.shp`; para usar otra cuenca: `--shp otra.shp`. Los días con horas faltantes no entran en los acumulados (el script avisa). Si unos pocos valores extremos dominan la escala de color, esta se satura en el percentil 99 (barra con flecha).

### 3. Comparación con ERA5 y PISCO

#### ERA5

**Una sola vez:**
1. Crear una cuenta en https://cds.climate.copernicus.eu.
2. Copiar el *Personal Access Token* desde https://cds.climate.copernicus.eu/profile.
3. Aceptar la licencia de *ERA5 hourly data on single levels*: pestaña **Download** de https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels, al final de la página. Sin esto, la descarga falla con un error de licencia.
4. Guardar la clave:
   ```bash
   python scripts/02_descargar_era5.py --clave TU-TOKEN
   ```
   Se guarda en `~/.cdsapirc`, **fuera del repo**. Nunca la peguen en un script ni la suban.

**Descargar, pasar a diario y comparar** (2005, 2010 y 2015; o indicar un año):
```bash
python scripts/02_descargar_era5.py          # 4 pedidos por año (feb, mar, abr y 1-may), unos MB
python scripts/03_diario_obs.py era5         # mismo día pluviométrico que SAAG
python scripts/08_comparar.py era5
```

La descarga cubre 4.25–5.5°S y 74.25–72.75°W, alineada a la malla de 0.25° de ERA5 e incluyendo las celdas del borde. Cada pedido espera en la cola de Copernicus: puede tardar de segundos a varios minutos. Si se corta, al relanzar salta los meses ya descargados.

Cómo se compara:
- **Media de la cuenca:** en SAAG, el promedio de sus 330 celdas de 4 km. En ERA5, el promedio de sus celdas de 0.25° ponderado por el área que cae dentro de la cuenca (unas 14 celdas, equivalentes a ~6 completas).
- **Mapas:** el SAAG también se promedia en la malla de ERA5, para que la diferencia SAAG − ERA5 sea entre campos de la misma resolución.

Salidas en `figures/`:
- `era5_comparacion_resumen.csv`: totales, sesgo (mm y %), correlación diaria y semanal, RMSE, días lluviosos, días de más de 20 mm, percentil 95 y máximos.
- `era5_comparacion_mensual.csv`: acumulado de cada mes en SAAG y ERA5.
- Figuras: series diarias (`era5_comparacion_serie.png`), barras mensuales (`..._mensual.png`), dispersión y curva de excedencia (`..._dispersion.png`) y mapas (`..._mapas.png`).

ERA5 no es una observación: es el reanálisis que fuerza al WRF. La comparación responde la pregunta 4 (¿qué aporta resolver la convección a 4 km?), no si el modelo acierta. Para eso hace falta PISCO o IMERG.

#### PISCO (referencia observacional)

PISCOp v2.1 (SENAMHI) versión *stable* tiene datos diarios de 1981 a 2016, a 0.1°. Se descarga recortado desde la [IRI Data Library](https://iridl.ldeo.columbia.edu/SOURCES/.SENAMHI/.HSR/.PISCO/.Prec/.v2p1/), **sin cuenta**:
```bash
python scripts/02b_descargar_pisco.py        # FMA 2005, 2010 y 2015 (+1 día a cada lado), unos kB
python scripts/03_diario_obs.py pisco
python scripts/08_comparar.py pisco
```
Si la descarga falla (por ejemplo por la red de la universidad), el script imprime la URL. Ábranla en el navegador y guarden el archivo como `data/raw/pisco/pisco_pr_<año>.nc`.

**Fechas:** PISCO ya viene diario. Por convención de SENAMHI, el día D es la lluvia de 07:00 de D a 07:00 de D+1, igual que nuestro día pluviométrico, pero no está confirmado cómo etiqueta PISCO la fecha. Por eso `08_comparar.py` imprime la correlación con SAAG desplazando PISCO −1, 0 y +1 días. Si el máximo no está en 0, el script indica qué valor poner en `PISCO_DESFASE_DIAS` (`scripts/config.py`); luego hay que rehacer `03_diario_obs.py pisco` y la comparación.

Salidas: `figures/pisco_comparacion_*`, iguales a las de ERA5. Con PISCO sí se evalúa el modelo (preguntas 1–3), con la cautela de que en el llano amazónico PISCO tiene pocas estaciones y depende más del satélite.

#### IMERG

`python scripts/03_diario_obs.py imerg <año>` con los archivos en `data/raw/imerg/<año>/` (ver `docs/datos.md`). La comparación con `08_comparar.py imerg` queda para cuando esos datos estén descargados.

### 4. Comparación con estaciones y PISCO v3

```bash
python scripts/10_estaciones.py
```
Usa `figures/estaciones_obs_pisco3_diaria_FMA.csv` (observado y PISCO v3 en Genaro Herrera y Bagazán) y los `.nc` de SAAG. Toma WRF-SAAG en la celda de 4 km más cercana a cada estación y genera `estaciones_diaria.csv`, `estaciones_resumen.csv` y las figuras `estaciones_precip_mensual.png` y `estaciones_dias_lluvia.png`.

### Corridas WRF del otro dominio (solo uso local)

Los archivos `WRF2d_CTRL_*.nc` son recortes de la misma simulación WRF-SAAG sobre otro dominio (15.6–7.7°S, 77.0–70.5°W: Ucayali alto y medio, con los Andes). La Intercuenca 49911 queda fuera de ese dominio.

```bash
python scripts/05_wrf_ctrl.py ~/Downloads                         # diario FMA, ciclo diurno y lluvia vs altura
python scripts/04_mapas_mensuales.py --fuente wrfctrl --combinado
```

Todos sus resultados (`wrfctrl_*`) están en `.gitignore` y **no se suben**.

## Cómo subir resultados al repositorio

Cada integrante sube **solo los archivos de su año**. Todos llevan el año en el nombre, así nadie sobrescribe a nadie.

| Archivo | Quién lo sube |
|---|---|
| `data/processed/saag_pr_diaria_FMA_<año>.nc` | quien extrajo ese año |
| `figures/mapas_total_<año>.png` | quien extrajo ese año |
| `figures/mapas_diaslluvia_<año>.png` | quien extrajo ese año |
| `figures/mapas_resumen_mensual_<año>.csv` | quien extrajo ese año |
| `figures/mapas_climatologia.png`, `figures/mapas_resumen_mensual_todos.csv` | solo la coordinación, al final |

**Para cada año** (ejemplo 2010):
```bash
git pull
python scripts/01_extraer_saag.py 2010 --workers 20
python scripts/06_subir_anio.py 2010
```
`06_subir_anio.py` comprueba que el `.nc` esté completo, genera los mapas y el CSV del año si faltan y sube **exactamente esos 4 archivos**. Si algunos ya estaban subidos, solo sube los que faltan.

**No suban archivos a mano ni usen `git add .`.** Así se olvida el `.nc` o se pisan las figuras combinadas.

**Al final (coordinación)**, con los tres `.nc` ya en el repo:
```bash
git pull
python scripts/04_mapas_mensuales.py --combinado
git add figures/mapas_climatologia.png figures/mapas_resumen_mensual_todos.csv
git commit -m "Climatología FMA 2005-2010-2015" && git push
```
Como los `.nc` están en el repo, esto no requiere volver a descargar nada.

## Configurar git (una vez por computadora)

1. **Aceptar la invitación** de colaborador en `https://github.com/rcrafa179/ucayali-precip-saag/invitations`.
2. **Iniciar sesión** con `gh auth login` (GitHub.com → HTTPS → navegador), o con un token *classic* que tenga marcado el permiso **`repo`**. GitHub no acepta la contraseña de la cuenta, y un token *fine-grained* puede no tener acceso a un repo de otra cuenta. Si `git push` responde `403 ... denied to <usuario>`, el token no tiene ese permiso: creen uno nuevo y borren el anterior con
   ```bash
   printf "protocol=https\nhost=github.com\n\n" | git credential reject
   ```
3. **Usar un correo verificado en GitHub**, para que los commits cuenten como suyos y aparezcan en *Contributors*:
   ```bash
   git config --global user.name "Nombre Apellido"
   git config --global user.email "correo-verificado-en-github@ejemplo.com"
   ```
   Si el correo que ya usaron no está en su cuenta, agréguenlo en GitHub → Settings → Emails. Los commits anteriores se les asignan solos.

## Reglas del grupo

- **Sí se suben:** `data/processed/saag_*`, `figures/` y `cuenca/`. **No se suben:** `data/raw/`, `wrfctrl_*` ni credenciales (`.cdsapirc`, `.netrc`). El `.gitignore` ya lo controla.
- Los resultados de cada año se suben directo a `main` con `06_subir_anio.py`. Para cambios en el código, mejor una rama (`git checkout -b nombre/tarea`) y un Pull Request.
- Los parámetros comunes (caja, años, meses, día pluviométrico, rutas) solo se cambian en `scripts/config.py`.
- Antes de hacer commit de un notebook, limpien las salidas pesadas o usen `nbstripout`.
- Los datos crudos están en **UTC**.

## Referencias

**Datos**

1. Rasmussen, R., Liu, C., Ikeda, K., Dominguez, F. (2022). *Multi-decadal Convection-permitting Simulation of Current Climate over South America using WRF* [dataset d616000]. NSF NCAR Geoscience Data Exchange. https://doi.org/10.5065/6XQW-ZB02
2. Dominguez, F., Rasmussen, R., Liu, C., Ikeda, K., Prein, A., et al. (2024). Advancing South American water and climate science through multidecadal convection-permitting modeling. *Bulletin of the American Meteorological Society*, 105(1), E32–E44. https://doi.org/10.1175/BAMS-D-22-0226.1
3. Hersbach, H., Bell, B., Berrisford, P., et al. (2020). The ERA5 global reanalysis. *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999–2049. https://doi.org/10.1002/qj.3803
4. Hersbach, H., Bell, B., Berrisford, P., et al. (2023). *ERA5 hourly data on single levels from 1940 to present* [dataset]. Copernicus Climate Change Service (C3S) Climate Data Store. https://doi.org/10.24381/cds.adbb2d47
5. Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., Tan, J. (2023). *GPM IMERG Final Precipitation L3 Half Hourly 0.1° × 0.1° V07* (GPM_3IMERGHH) [dataset]. NASA GES DISC. https://doi.org/10.5067/GPM/IMERG/3B-HH/07 (solo si se usa IMERG)
6. Autoridad Nacional del Agua (ANA). Delimitación y codificación de unidades hidrográficas del Perú (método Pfafstetter): Intercuenca 49911, Bajo Ucayali [shapefile `cuenca/49911.shp`].
7. Aybar, C., Fernández, C., Huerta, A., Lavado, W., Vega, F., Felipe-Obando, O. (2020). Construction of a high-resolution gridded rainfall dataset for Peru from 1981 to the present day. *Hydrological Sciences Journal*, 65(5), 770–785. https://doi.org/10.1080/02626667.2019.1649411
8. SENAMHI. PISCOp v2.1 *stable daily* (1981–2016), distribuido por la IRI Data Library, Columbia University. https://iridl.ldeo.columbia.edu/SOURCES/.SENAMHI/.HSR/.PISCO/.Prec/.v2p1/

**Modelo y configuración del WRF-SAAG**

9. Skamarock, W. C., Klemp, J. B., Dudhia, J., Gill, D. O., Liu, Z., Berner, J., Wang, W., Powers, J. G., Duda, M. G., Barker, D. M., Huang, X.-Y. (2019). *A Description of the Advanced Research WRF Model Version 4*. NCAR Tech. Note NCAR/TN-556+STR. https://doi.org/10.5065/1dfh-6p97
10. Esquemas físicos usados por el SAAG: microfísica de Thompson (Thompson et al., 2008, *Mon. Wea. Rev.*, 136, 5095–5115, https://doi.org/10.1175/2008MWR2387.1); capa límite YSU (Hong et al., 2006, *Mon. Wea. Rev.*, 134, 2318–2341, https://doi.org/10.1175/MWR3199.1); radiación RRTMG (Iacono et al., 2008, *J. Geophys. Res.*, 113, D13103, https://doi.org/10.1029/2008JD009944); suelo Noah-MP (Niu et al., 2011, *J. Geophys. Res.*, 116, D12109, https://doi.org/10.1029/2010JD015139).

**Convección explícita**

11. Prein, A. F., Langhans, W., Fosser, G., et al. (2015). A review on regional convection-permitting climate modeling: Demonstrations, prospects, and challenges. *Reviews of Geophysics*, 53(2), 323–361. https://doi.org/10.1002/2014RG000475

**Contexto de los años estudiados**

12. Marengo, J. A., Nobre, C. A., Tomasella, J., Oyama, M. D., et al. (2008). The drought of Amazonia in 2005. *Journal of Climate*, 21(3), 495–516. https://doi.org/10.1175/2007JCLI1600.1
13. Lewis, S. L., Brando, P. M., Phillips, O. L., van der Heijden, G. M. F., Nepstad, D. (2011). The 2010 Amazon drought. *Science*, 331(6017), 554. https://doi.org/10.1126/science.1200807
14. Marengo, J. A., Tomasella, J., Alves, L. M., Soares, W. R., Rodriguez, D. A. (2011). The drought of 2010 in the context of historical droughts in the Amazon region. *Geophysical Research Letters*, 38, L12703. https://doi.org/10.1029/2011GL047436
15. Espinoza, J. C., Ronchail, J., Guyot, J. L., et al. (2011). Climate variability and extreme drought in the upper Solimões River (western Amazon Basin): Understanding the exceptional 2010 drought. *Geophysical Research Letters*, 38, L13406. https://doi.org/10.1029/2011GL047862
16. Jiménez-Muñoz, J. C., Mattar, C., Barichivich, J., et al. (2016). Record-breaking warming and extreme drought in the Amazon rainforest during the course of El Niño 2015–2016. *Scientific Reports*, 6, 33130. https://doi.org/10.1038/srep33130
17. Panisset, J. S., Libonati, R., Gouveia, C. M. P., et al. (2018). Contrasting patterns of the extreme drought episodes of 2005, 2010 and 2015 in the Amazon Basin. *International Journal of Climatology*, 38(2), 1096–1104. https://doi.org/10.1002/joc.5224

**Estaciones y PISCO v3**

18. Gutiérrez, L., Lavado-Casimiro, W. (2025). *PISCOp v3.0: Actualización de datos grillados de precipitación diaria (1981–2025)*. Servicio Nacional de Meteorología e Hidrología del Perú (SENAMHI).
19. ANA – SENAMHI. Plataforma ANDREA: precipitación diaria de las estaciones Genaro Herrera y Bagazán.
