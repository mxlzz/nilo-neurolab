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
