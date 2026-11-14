# Plan de trabajo

Marcar con `[x]` al terminar. Responsable entre corchetes.

## 0. Organización
- [ ] Confirmar entregables con los organizadores del taller [ ]
- [ ] Todos clonan el repo y crean el entorno [todos]
- [ ] Reparto por año: 2005 [ ] · 2010 [ ] · 2015 [ ]

## 1. Cuenca
- [ ] Descargar el límite del Ucayali (ANA o HydroBASINS) a `data/aux/` [ ]
- [ ] Verificar que la caja de `config.py` cubre toda la cuenca [ ]

## 2. Prueba piloto del SAAG
- [x] Confirmar la ruta de los archivos en el catálogo THREDDS (`hist2D/<YYYYMM>/`) [Rafael]
- [ ] `python scripts/01_extraer_saag.py prueba`: variable, unidades, tiempo por hora [ ]
- [x] Variable = `PREC_ACC_NC` · unidades = mm · acumulación = 60 min (ya horaria) · caja = 365 × 251 puntos [Rafael]
- [ ] Medir s/hora por OPeNDAP con el modo `prueba` = ____

## 3. Extracción del SAAG (máquina del grupo, en tmux)
- [ ] 2005 [ ]
- [ ] 2010 [ ]
- [ ] 2015 [ ]
- [ ] Control de calidad: horas faltantes, negativos, reinicios de acumulación [ ]

## 4. Datos de referencia
- [ ] IMERG 2005 / 2010 / 2015 [ ]
- [ ] ERA5 2005 / 2010 / 2015 [ ]
- [ ] PISCO [ ]

## 5. Homogeneización
- [ ] Hora local (UTC−5) y máscara de cuenca [ ]
- [ ] Regrillado conservativo WRF → 0.1° (xESMF) [ ]
- [ ] IMERG 30 min → horario; ERA5 en m → mm [ ]
- [ ] Agregados diarios, mensuales y estacionales en `data/processed/` [ ]

## 6. Análisis descriptivo
- [ ] Mapas de acumulado anual y estacional (DJF, JJA) por año y producto [ ]
- [ ] Series mensuales del promedio de cuenca [ ]

## 7. Ciclo diurno
- [ ] Mapas de la hora del máximo y de la amplitud (WRF vs. IMERG) [ ]
- [ ] Ciclo diurno promedio: llano vs. vertiente andina [ ]

## 8. Intensidad, extremos y altitud
- [ ] Frecuencia, intensidad, P95, P99, PDF [ ]
- [ ] Métricas por bandas de altitud (HGT) [ ]

## 9. Validación
- [ ] Sesgo, RMSE, correlación, KGE (serie de cuenca) [ ]
- [ ] POD, FAR, CSI horarios (umbrales 0.1, 1 y 5 mm/h) [ ]
- [ ] FSS espacial [ ]

## 10. Interanual
- [ ] Anomalías de 2005, 2010 y 2015 respecto a la climatología (IMERG o PISCO) [ ]

## 11. Síntesis
- [ ] Figuras finales en `figures/` [ ]
- [ ] Informe o presentación [ ]
