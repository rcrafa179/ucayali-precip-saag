# Plan de trabajo — precipitación diaria, FMA de 2005, 2010 y 2015

Marcar con `[x]` al terminar. Responsable entre corchetes.

## 0. Organización
- [ ] Confirmar entregables con los organizadores del taller [ ]
- [ ] Todos clonan el repo y preparan el entorno [todos]
- [ ] Reparto por año: 2005 [ ] · 2010 [ ] · 2015 [ ]

## 1. Cuenca
- [x] Dominio fijado: 5.3–4.4°S, 74.0–73.0°W (Ucayali bajo, Requena–Nauta) [Rafael]
- [ ] Opcional: límite de la cuenca o del cauce en `data/aux/` para los mapas [ ]

## 2. Prueba piloto del SAAG
- [x] Ruta de archivos en THREDDS: `hist2D/<YYYYMM>/` [Rafael]
- [x] Variable = `PREC_ACC_NC` · mm · acumulación de 60 min · dominio = 28 × 30 puntos [Rafael]
- [x] Lectura recortada por OPeNDAP: ~2–6 s por hora [Rafael]
- [ ] Confirmar la convención de fecha de PISCO y fijar `DIA_INICIO_UTC` en `config.py` [ ]
- [ ] `python scripts/01_extraer_saag.py prueba` (un día completo) [ ]

## 3. Extracción del SAAG, diario FMA
- [ ] 2005 [ ]
- [ ] 2010 [ ]
- [ ] 2015 [ ]
- [ ] Control de calidad: días con `n_horas < 24`, valores negativos o extremos raros [ ]

## 4. Datos de referencia (solo FMA)
- [ ] PISCO diario [ ]
- [ ] IMERG 30 min, del 1 de febrero 12 UTC al 1 de mayo 12 UTC de cada año → `03_diario_obs.py imerg` [ ]
- [ ] ERA5 horario → `03_diario_obs.py era5` [ ]

## 5. Homogeneización
- [ ] Máscara de cuenca para SAAG, PISCO, IMERG y ERA5 [ ]
- [ ] Regrillado conservativo del SAAG (4 km) a 0.1° con xESMF, para comparar con PISCO e IMERG [ ]
- [ ] Verificar que las fechas coincidan entre productos (mismo día pluviométrico) [ ]

## 6. Análisis descriptivo
- [ ] Mapas del acumulado FMA por año y producto [ ]
- [ ] Mapas del acumulado mensual (F, M, A) [ ]
- [ ] Serie diaria del promedio de cuenca (todos los productos en un gráfico, por año) [ ]

## 7. Frecuencia, intensidad y extremos diarios
- [ ] Días lluviosos (≥ 1 mm), intensidad media en días húmedos (SDII) [ ]
- [ ] P95 y P99 diarios, Rx1day, Rx5day [ ]
- [ ] PDF de la precipitación diaria [ ]
- [ ] Métricas por bandas de altitud (HGT): vertiente andina vs. llano [ ]

## 8. Validación
- [ ] Sesgo, RMSE, correlación y KGE de la serie diaria de la cuenca [ ]
- [ ] Mapas de sesgo relativo y correlación por punto [ ]
- [ ] POD, FAR y CSI diarios (umbrales 1, 10 y 20 mm/día) [ ]
- [ ] SAAG vs. ERA5: ¿la resolución de 4 km mejora al forzante? [ ]

## 9. Comparación entre años
- [ ] Diferencias del acumulado FMA entre 2005, 2010 y 2015 en cada producto [ ]
- [ ] Anomalías respecto a la climatología FMA de PISCO (1981–2016) [ ]

## 10. Síntesis
- [ ] Figuras finales en `figures/` [ ]
- [ ] Informe o presentación [ ]
