# Auditoría documental — 24/11/2026

Corte [c0c06c95c176eb9c0e0df71853313d16acda0f27](https://github.com/mxlzz/Nilo_public/commit/c0c06c95c176eb9c0e0df71853313d16acda0f27). Árbol no truncado: 265 archivos docs/neurolab (60 resultados), 196 experiments/neurolab (86 tests), 53 workflows neurolab-*; 514 archivos, 5.415.507 bytes. Revisión de estado, fundamentos, gates, cierres, evidencia central, código pertinente y CI H08b.19. No inspección línea por línea ni reproducción independiente.

## N, campañas concluidas
E00–E08: G00 suficiencia prototipo con divergencias, G01 determinismo/restauración, G02 WTA, G03 asociación/reversión breve, G04 doble escala aislada, G05 no superada, G06 detector conjuntivo fijo (no concepto aprendido), G07 recableado iguala LRU, G08 recurrencia elemental no pensamiento. E09 cerrada parcial/negativa, G09 no superada. Ver [cierre E09](inherited/docs/neurolab/E09_CIERRE_FORMAL_RESULTADO_20261122.md).
TAB1/TAB2 equivalencia exacta E06/E03 con tablas mismas features. I3c7h recompensa contingente discrimina, I3c7i lesión STW afecta decisión local, R-ACT-I3c no superado. I3c7g mayor horizonte insuficiente. I3c7k oráculo STW→LTW +4.90pp IC95 [.83,8.91]pp frente gate +10pp; congelar C1ContextBrain 8 contactos. [Cierre estratégico](inherited/docs/neurolab/E09_02I_I3C7L_CIERRE_ESTRATEGICO_LINEAS_H_N.md). [Errata E09.00R](inherited/docs/neurolab/E09_00R_RECONCILIACION_GATES_20261122.md) prevalece: G05 crédito temporal, G09 síntesis cerebro aislado.
NR01: 20 mundos desarrollo 23000..23019, 320 condiciones; FIFO1-NN16 S=.812083, KMeans4 .847396 (+3.53pp vs gate +5pp), +34% estado, reversión .4875 vs 1.0; ART excede 16 categorías en104/120. STOP sin confirmación. [Informe](inherited/docs/neurolab/NR01_04_06_RESULTADO_Y_CIERRE_20261122.md).
G05-INFO detectó asimetría informacional. G05-NX01: TK 1.0 en 20 mundos, imposible +.05; brazos neuronales C/F/P NO ejecutados. STOP del banco, no refutación de red. [Informe](inherited/docs/neurolab/G05_NX01_RESULTADO_Y_STOP_20261122.md). Reservas 1400..1419, 24000..24019, 26000..26019 no consumidas según registros. No tuning.

## H
GEN/EXE Build47 y medio original inspeccionados, arranque legítimo operativo Windows remoto con CD montado, DDE y sujeto único. Viejos bloqueos no vigentes en origen; acceso en destino aún por verificar. H08b.11/.12 ruta alternativa química→cerebro (29 ciclos, 19 snapshots pareados); .13 ruta regular cerebro→química→conducta (15 ciclos). Cadencia física sin instrumentación y fidelidad global no demostradas; G-H6-CLOCK abierta.
H08b.14 pulso transportado sin oportunidad de escritura; .15 candidatos; .16–17 coincidencia local sin escritura positiva discriminante. .18 STW: 27 aumentos (17 clase1 primarios, 10 clase0 exploratorios), 512 pares exactos, E0 no oportunidad, Z sin incremento, no sham aleatorizado. selected_type Z erróneo por bucle; clase0 corregida analíticamente, crudo intacto. [Informe](inherited/docs/neurolab/H08B_18_RESULTADO_ESCRITURA_DISCRIMINANTE_20261124.md).
H08b.19 [CI 45492676512](https://github.com/mxlzz/Nilo_public/actions/runs/45492676512), job 138794825967 SUCCESS; JSON leído: tick512, 256/256 exactos, slot9 (96,7,0,9)→(100,7,1,9), contrafactual LTW rate0 no aumenta; 29 incrementos LTW +1. 1792/1792 acumulados siete sesiones con snapshots (slots correlacionados). STW y LTW en individuos distintos; no adquisición/retención de misma asociación ni intervención causal. [Informe](inherited/docs/neurolab/H08B_19_RESULTADO_CONSOLIDACION_LTW_20261124.md). No ensayo pendiente en marcador actual.

## Método y alternativas
Fortalezas: prerregistro, controles, ablaciones, conservación de negativos y STOP. Riesgos: sobreajuste, features prefijadas, filtro de oportunidad no prevalencia, forcing, tiempos instrumentados, pseudorreplicación, insumos privados y artefactos efímeros. No repetir H08b.16–19 ni diseñar motor nuevo. [CDR](https://double.nz/creatures/brainutilities.htm), [CAOS](https://www.caoschaos.com/docs/index.html), [openc2e](https://github.com/openc2e/openc2e) referencia no oráculo; [tres factores](https://pmc.ncbi.nlm.nih.gov/articles/PMC6079224/) y [Benna–Fusi](https://www.nature.com/articles/nn.4401) candidatos, no soluciones validadas. Reutilizar revisiones I3c8 y NR01; no adoptar todavía. GO H08c.0, STOP N.

Preservación histórica: ocho ZIP E09 y NR01 en Drive con hashes según informes, trazas secundarias temporales. No se verificaron bytes de Drive en esta intervención; mantener referencias y acceso privado. No publicar originales. Ver MIGRATION.md y manifiestos.

## Cierre operativo NL-M
514/514 archivos presentes, 513 exactos y una excepción de privacidad. 979 runs NeuroLab inventariados por fecha; 532 artefactos SHA verificado y 559 logs archivados. 374 runs aún sin cobertura binaria, 15 artefactos y 18 logs no copiados por presupuesto, 28 logs H deliberadamente excluidos. Resultados clave conservados, sin bloqueo conocido para H08c.0. Ver [verificación](evidence/MIGRATION_VERIFICATION.md) y [cobertura](evidence/ARCHIVE_COVERAGE.json). No afirmar conservación exhaustiva ni auditoría científica independiente.

## H08c.0 — revisión de cierre (autoverificación, 24/11)
GO documental a [H08c.1](protocols/H08c.1.md), condicionado a acceso original y observación válida. Evidencia nativa permite proponer TRIG sensorial (no demostrado en Build47), CHEM ya entregado y DDE agregado limitado; no confundir índice Concept con identidad o firing Decision con elección. Contrato discrimina contingencia frente a dosis, estado químico y actividad, conserva STOP por ausencia de oportunidad y límite de costo. Revisión de diseño, no ejecución ni resultado causal; H08c.2 aún requiere prerregistro definitivo y potencia tras piloto. Riesgo mayor: sincronización post-WTA, persistencia de señales químicas endógenas y estabilidad de fuentes; si no identificables, STOP. N y reservas intactas. Valor marginal: testar asociación, no más testigos de peso. No auditor independiente disponible en esta intervención.


## H08c.1 preflight parcial (24/11)
Tres insumos originales verificados por hash local, CD pendiente de verificación actual por límite de conector. Nuevo punto post-WTA respaldado por inspección estática, pendiente de validación dinámica y temporal (Decision anterior a Concept en loop). No prueba de asociación ni cambio de gate. No exponer valores de secretos, archivos originales o IDs adicionales; preservar configuración existente. [Evidencia](evidence/H08c.1_PREFLIGHT_20261124.md).

CI #45516662183 confirmó ambos secretos ausentes; bloqueo de ejecución, no resultado científico. Sin gasto pago ni originales publicados. Autoverificación.

Readiness revalidado tras intervención: ambas configuraciones presentes. No equivale a acceso ni integridad en Windows; nuevo preflight limitado a hash, montaje y CDB, sin sesiones científicas.

Preflight original en destino PASS: CI 45517841268, evidencia efectiva de hashes, montaje y limpieza. No se ejecutó juego. TRIG estático escribe input; no prueba transmisión a decisión; Concept640 y orden Decision antes de Concept obligan a asociar fuentes por firma y ciclo. No modificar gates.

H08c.1 sesión 1 preregistro técnico: validación WTA exacta, identidad y marcadores nativos, firma Concept con fuentes, ventana lógica y lavado; interacción CDB/ReadProcessMemory aún no validada. Cualquier fallo se conserva como instrumental; sin prometer PASS.

H08c.1 sesión 1 NO supera gate (CI verde, cero eventos). Artefacto cotejado, sujeto creado y limpieza confirmada. No se conocen causas exactas de timeout. Una corrección instrumental permitida, no tuning ni cambio de criterios. Ver evidence/H08c.1_session1_result.md.

Corrección única CDB batch, patrón de transporte heredado, no atribuir causalmente timeout a buffering. Tests sintéticos nuevos y control de captura; si falla, STOP. No afirmación de equivalencia dinámica hasta validar datos.

## H08c.1 cierre STOP (autoverificación)
Dos fallos instrumentales, 2/3 arranques, ~7 min. Segunda corrección no permitió recuperar eventos aunque CDB ready y salida local; causa exacta no identificada. No hay evidencia de capacidad/incapacidad de aprendizaje. Déficit de diseño: complejidad del parser y ausencia de diagnóstico sanitizado mínimo de líneas; no ocultar. Tercer arranque sin valor para gate; no ejecutar. H08b.18/.19 intactas. Decisión sustantiva requerida antes de nueva campaña. [Cierre](evidence/H08c.1_STOP.md).

H08d autorizado. Se identifica diferencia de escape y parser entre instrumentos, hipótesis no causa demostrada. Probar con CDB real sobre fixture propio antes de originales. Presupuesto y STOP explícitos; sin cambios de alcance o gate.

H08d.D0: el diseño de control compartió marcadores entre variantes y la negativa contaminó el conteo, por lo que no supera su propio gate. Diagnóstico reproducido en fixture real, no prueba retrospectiva de causalidad en C1. STOP formal; D0b es nueva pregunta de aislamiento, con el mismo criterio estricto, sin ampliar presupuesto ni alcance. D2 diferida.

D0b control aislado PASS; se valida transporte en fixture, no retrospectivamente el motor. GO D1 bajo contrato mínimo. D0 FAIL histórico intacto. D2 diferida.

D1 preregistro tras D0b: captura reducida, selección exacta con empate/exclusión/bypass, identidad y oportunidad. El resultado no valida aprendizaje, ni se trata cada ciclo como sujeto independiente.

## H08d cierre
D0 FAIL formal, D0b PASS y D1 PASS local 20/20. Transporte aislado y lectura libre post-WTA recuperados. Una sesión; no validación de empate/bypass en runtime, ni comportamiento, aprendizaje, retención, TRIG o lavado. Costo 3/3 jobs, 214s y 1 arranque. D2 diferida por decisión técnica tras D0; no más ejecución en presupuesto. [Dictamen](evidence/H08d_D1_result.md). Autoverificación, no auditor independiente. N STOP.

D2 autorizado: fuente histórica CELL especifica output/state; contraste inmediato en mismo macro, dos shams, basal elegible y verificación identidad. Un sujeto, no cuatro independientes. Sin afirmación de simultaneidad ni lavado. Cierre al fallo, no tuning.

D2 cierre (autoverificación): gate de entrega local 4/4, dos pulsos exactos, dos shams sin subida. No separación temporal: A 32/32 antes y después de B. CHEM51/54/55 no cero; ins# opcional falló. No afirmar actividad lógica, ausencia de refuerzo ni propagación. Una sesión, presupuesto cerrado. Próxima revisión documental; no nueva ejecución ni reabrir N.

D3.0 autoverificación: evidencia estática y fórmula heredada permiten predicción discriminante de decaimiento, no explicación demostrada de D2. No confundir contador de sujeto con brain updates; output precede relajación. D3.1 propuesto con límite 1 job, no ejecución. H08c.1/N STOP, G05/R-ACT-I3c/G09 no superadas.

D3.1 revisión previa: EXE/GEN releídos por hash, cinco puntos estáticos, transporte D0b y lectura D1 reutilizados. Captura de ambas rutas, controles de continuidad, identidad y predicción. Sin modificación de criterios ni ejecución de aprendizaje.

D3.1 cierre (autoverificación): 9/9 predicciones exactas con 8 ciclos basales, identidad y ruta válidas; estímulo natural transitorio sin reset. 1 sujeto, no 9 réplicas. No resuelve causa D2 ni lavado de química ni aprendizaje. Un job 144s y un arranque, presupuesto agotado. GO documental D4, ejecución condicionada. H08c.1/N STOP.

D4.0 autoverificación: mapa derivado del bucle original y flags/counts genéticos, no selección post hoc. Gate exige layout efectivo y predicción de copia/umbral, canales opuestos y separación local; no sustituye gate H08c.1, no inferir Concept/Decision ni lavado. No ejecutado.

D4.1 previa: ampliar D3 solo con layout, COPY/PERCEPTION y segundo pulso condicionado a A y basal adicional. No medir Concept ni aprendizaje, no aumentar presupuesto. H08c.1/N STOP.

D4.1 cierre (autoverificación): 34 ciclos contiguos, 18/18 predicciones de propagación exactas y 16/16 basal cero, layout efectivo. Una sesión; no prueba exclusividad global, Concept, Decision contingente, química o aprendizaje. Recálculo separado, no réplica. 157s, 1 job/1 arranque, presupuesto agotado. GO documental D5, sin nueva ejecución hasta aprobación.

D5.0 autoverificación: ANDTYPE0 no es min/producto; predicción depende de outputs y STW reales. Selección previa de singleton y control evita búsqueda retrospectiva; si no hay oportunidad, STOP, no inferir ausencia general de representación. Sin ejecución, aprendizaje no demostrado. H08c.1/N STOP.

## Revisión de alineación con Nilo — 25/11/2026
Usuario confirma continuidad con límite estratégico: H sirve a aprendizaje neuronal autónomo por experiencia; no es fin histórico. D1/D2/D3/D4 y H08b.18/.19 son testigos locales, no mente ni memoria aprendida. E09 parcial/negativa y baselines simples impiden asumir superioridad. Próximo hito científico: experiencia modifica decisión futura y persiste con dinámica activa sin premio; D5 y D6 únicamente si desbloquean ese contraste. No multiplicar ensayos microscópicos por inercia; cerrar H con límites si valor marginal insuficiente. Sin cambios de objetivo, gates, ni autorización de reapertura N. D5.1 aprobada dentro de presupuesto previamente propuesto.

D5.1 revisión previa: relectura estática y fuentes CDB, control por topología sin selección de respuesta. No ampliar alcance ni presupuesto. STOP al fallo/no oportunidad, no iterar por inercia.

## D5.1 cierre y valor marginal
Formal FAIL por upstream B, no por instrumento; evidencia Concept selectiva condicional 54/54 y topología estable, un sujeto, control negativo sin oportunidad positiva. No confundir con aprendizaje, ni ausencia de premio administrado con química cero. No explicar causa de desaparición entre fases sin observación. Presupuesto agotado, no repetir. D6 automático no autorizado. Recomendar decidir entre único contraste integrado con estímulo efectivamente observado y controles de oportunidad de aprendizaje, o cierre H parcial; no nueva microcampaña por inercia. Autoverificación.

D5x previa: valor directo para separación sensorial/crédito temporal; hipótesis estática fuerte de reset contextual, no prueba de causa pasada. Contraste focalizado de callsite, control temporal e identidad, sin nueva campaña microscópica extensa; N STOP y D5.1 FAIL intactos.

## D5x cierre (autoverificación)
Gate formal NO OPORTUNIDAD, no fallo instrumental. Cambio de atención confirmado y escritura de cero 32/32, con testigo endógeno positivo en L5:12, fuera de pulsos. A/B normales 18/18. D5.1 no reclasificada ni causa histórica demostrada. Decisión: cerrar microdiagnóstico, incorporar registro de cambios de atención al diseño de D6 integrado; no intentar controlar por forcing ni buscar coincidencia por repetición. Un sujeto, 151s, presupuesto cerrado. No N ni integración.

D6.0 revisión (autoverificación): pregunta directa de oportunidad para adquisición/retención; no exigir decaimiento pasivo tras evidencia de reset, no sustituir gate D5.1. Controles sham, lag, topología previa, WTA y contraste de sensibilidad sin administrar premio. Riesgos: coste escaneo/captura y marcador sham no validado; STOP antes de originales si implementación no interpretable. Un piloto no demuestra dependencia causal de elección ni aprendizaje. Si no factible proponer cierre H parcial, no más microcampañas; aprobación de ejecución requerida.

D6.1 previa: relectura estática PUTV y química, reutilización de observadores probados, registro completo de topología y selección fija; fixture propio para comando de lectura de archivo y sintaxis, STOP si falla. Riesgo de costo y oportunidad explícito. No alterar gate.

## D6.1 cierre (autoverificación)
Formal instrumental_incomplete; no inferir fallo científico de aprendizaje. Fixture validó script/transport, no captura integrada. Un error de marcador no identificable desde derivado, ciclo sin ENDC. Además, inventario 640 filas verificable, ninguna conexión singleton hacia A40, por tanto precondición topológica ausente aunque se corrigiera parser; otra sesión o selección multientrada sería nuevo contrato. 0 exposiciones, no oportunidades STW medidas. No rescatar, 162s, límite de job agotado. Recomendar cierre H parcial/síntesis, no reabrir N sin nueva pregunta y autorización.

## Síntesis estratégica H (autoverificación)
Mecanismos locales separados de aprendizaje integrado; no G09 PASS. D6 captura incompleta y topología faltante impiden contrastar adquisición; no justifica otro arranque bajo contrato previo. Error de generación corregido antes de ejecutar, no confundir con captura posterior. Alternativas H nuevo contrato / N documental / STOP evaluadas; se recomienda pausa H parcial y revisión documental N independiente, sin implementación ni cambio de gates. Archivo parcial, sin auditor independiente. Pendiente aprobación sustantiva del usuario. [Informe](evidence/H_PARTIAL_SYNTHESIS_20261125.md).

## Replanteo H — decisión aprobada (autoverificación)
Se reemplaza la recomendación de cierre, no los resultados. Priorizar asociación aguas abajo con control contingente/yoked; TRIG8 ya era alternativa H08c no ejecutada, no prueba de concepto adquirido. D6 inviable en sujeto observado y captura incompleta no implican limitación del cerebro original. Menor carga de observación; nueva instrumentación, latencia, oportunidad y química aún sin validar. Contrato H09.1 previo, no ejecución ni presupuesto nuevo autorizado. H08c.1/D6 cerradas, N STOP y gates intactos. [Revisión](protocols/H_REFRAME_20261125.md).

## H09.1 previa (autoverificación)
Revisión estática y aritmética, sin datos nuevos del motor. El gate anterior de pulso único podía no ofrecer sensibilidad STW desde sus0; nuevo tren fijo de seis pulsos, no garantía de incrementos. Selección basal pretratamiento explicitada, población condicional, no selección por respuesta. Fixture valida bloques/guardas y formas completas antes de originales, diagnósticos sanitizados de líneas malformadas, latencia de feedback inocuo no equivalente a CHEM. Riesgos: cadencia 36 macros, estabilidad de firma y química endógena, presupuesto; STOP sin rescate. Contrato propuesto, no implementación ni ejecución. Aprobación requerida; no N ni cambios de puertas.

H09.1 previa a ejecución: aprobación confirmada. Relectura estática y fuente Microsoft de $vvalid/.writemem; guardas, inventario único, separación de selección y lectura, Q estricto respecto de ecos. No publicar dumps. Validar fixture y modelos antes de original; no rescatar gate ni exceder presupuesto.

## H09.1 cierre (autoverificación)
NO OPORTUNIDAD, no fallo instrumental: 25/25 WTA, inventario válido, un destino basal disponible. Criterio de dos destinos impide empezar, no resultado de aprendizaje. Observación seleccionada TRIG8 y cadencia no ejecutadas; fixture no demuestra su viabilidad nativa. Recálculo separado de inventario y WTA, sin auditor independiente. Exploratorio solapamiento estructural con segundo destino, no prueba oportunidad causal. Presupuesto cerrado. Próxima revisión documental de alternativa que mida cambio contextual de preferencia dominante; no relajar gate ni repetir, aprobación para nuevo contrato, N STOP.

H09 revisión de valor marginal: considerar cambio de preferencia dominante por contingencia inhibitoria con controles contra supresión global, no respuesta y deriva, basado en C1 clase1 y evidencia previa. Resultado H09.1 no reclasificado, no atribuir aprendizaje. Margen de decisión, química y presupuesto pueden impedir contraste: auditar factibilidad antes de código; nuevo contrato requiere aprobación. N STOP. Autoverificación.

## H09.S cierre (autoverificación)
Criterio previo cumplido: cota condicional de inhibición con fuente32, local31 y conexiones fijas incluso incluyendo fuerza0, no cubre margen basal mínimo; no prueba imposibilidad general ni causalidad. Corrección de saturación auxiliar antes de cierre sin alterar resultado principal; hashes, roundtrip y script reproducible. Cero arranques, N STOP. Evaluar opción poblacional solo documental, no otro contrato por inercia; no auditor independiente.

## H09.P cierre (autoverificación)
Criterio STOP predefinido cumplido: cota favorable k9/512 alcanza solo2/23 márgenes durante entrenamiento, ninguna tras lavado y probe, no resultado causal ni imposibilidad global. Error GraphQL de ref reconciliado; script y resultado verificables. Patrón natural no demostrado con datos disponibles; propuesta de una última factibilidad de solo lectura (H09.N0), no habilita entrenamiento, presupuesto y aprobación nueva. N STOP, H09.1/S no reclasificadas. Sin auditor independiente.

H09.N0 previa: aprobación confirmada, controles de transporte y límites, clasificación temporal sin selección por respuestas, endpoint no equivale a estabilidad continua; T completo requiere 256 ciclos. No GO por recurrencia aislada. Sin nuevo entrenamiento/N.

## H09.N0 cierre (autoverificación)
Transporte válido; NO OPORTUNIDAD por falta de B y Q, no falla de aprendizaje. WTA exacta y cambios de topología/pesos/fuerza en endpoints no implican adquisición ni causalidad. Proyección parcial (soportes, WTA, química, diferencias de fuentes), ZIP íntegro descargado, hashes/CRC. Un único sujeto y ventana; no generalizar. Refinamiento pre-run de factibilidad con endpoints sin afirmar crédito, sin efecto sobre conclusión. Presupuesto agotado, límite de campaña alcanzado. Recomendar cierre H parcial; N STOP, sin reintentos ni apertura automática. Sin auditor independiente.

## Cierre parcial H aprobado (autoverificación)
H09.N0 última observación según límite acordado. Se formaliza cierre parcial, no fidelidad ni refutación del aprendizaje original; preservar negativos y cobertura parcial. Revisión de orientación exclusivamente documental, no reabrir N sin aprobación discriminante. Sin auditor independiente.
