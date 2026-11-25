# H — síntesis parcial y decisión de continuidad (25/11/2026)

## Dictamen
D6.1 cerrado sin exposiciones; H queda en pausa operativa, no reconstrucción histórica completa. N sigue STOP. La recomendación sometida al usuario es cerrar la campaña histórica actual con alcance parcial y autorizar únicamente un examen documental de factibilidad de una nueva hipótesis N. No es aprobación de una implementación, ni G09 PASS. El criterio rector es OBJECTIVE.md y el límite estratégico acordado en PLAN.md.

## Matriz de mecanismos y evidencia
| Mecanismo | Evidencia y alcance | Implicación investigable / límite |
|---|---|---|
| Selección WTA | [D1](H08d_D1_result.md): 20/20 ciclos; D6: un par local exacto, sin ciclo integrado | Decisión discreta verificable; no asociación adquirida. |
| Entrada, persistencia y decaimiento | [D2](H08d_D2_result.md) entrega 4/4, carryover; [D3.1](H08d_D3.1_result.md) 9/9, cero estado en 8 actualizaciones, salida en 9 | Separar escritura, actualización, lectura y tiempo lógico. No asumir cadencia física ni química nula. |
| Propagación sensorial | [D4.1](H08d_D4.1_result.md) 18/18 dos canales 5:8/9→0:40/41 | Representación inicial dependiente de estado; no prueba de exclusividad global. |
| Concept | [D5.1](H08d_D5.1_result.md) 54/54 predicciones condicionales, selectividad A/B local; gate FAIL por extinción B | Conectividad y pesos reales condicionan oportunidad; no aprender representaciones ni confundir fórmula con adquisición. |
| Reset contextual | [D5x](H08d_D5x.1_result.md) 32 pares CLEAR, testigo activo 183/175→0/0 en GeneralSense12, asociado a cambio de atención; gate NO OPORTUNIDAD del estímulo inyectado. Borrado Decision/Source por lectura estática | Separar estado transitorio de memoria; registrar límites de contexto. No afirmar que se borran trazas de elegibilidad o pesos ni atribuir retrospectivamente causa de D5.1. |
| Orden de fases y química | H08b.13: rutas regular y alternativa; H08b.14: testigos de entrega CHEM49/50 | Orden de escritura y lectura puede cambiar inferencias. No equiparar ticks de sujeto con actualizaciones cerebrales. |
| Plasticidad y consolidación | [H08b.18](../inherited/docs/neurolab/H08B_18_RESULTADO_ESCRITURA_DISCRIMINANTE_20261124.md) 27 incrementos STW; [H08b.19](../inherited/docs/neurolab/H08B_19_RESULTADO_CONSOLIDACION_LTW_20261124.md) 29 incrementos LTW +1. Sesiones/sujetos distintos, 1792 pares exactos en conjunto de comparaciones, no muestras independientes | Testigos locales de actualización; no vínculo causal con conducta adquirida, retención activa, transferencia o crédito correcto. |
| Cadena integrada | [D6.1](H08d_D6.1_result.md) 640 filas Concept, cero singleton hacia A40, dos hacia B41, contraste no factible en ese sujeto. Captura instrumental incompleta D6_malformed1; no ENDC, no inventario Decision, 0/6 brazos | No prueba negativa de aprendizaje original. Conectividad observada variable entre D5/D6; sin estimar prevalencia, no inferir ausencia de rutas multientrada. |

## Contraste con N ya realizado
- E09 parcial/negativa: determinismo, WTA, asociación/reversión breve y dos escalas locales no implican retención activa robusta. TAB1/TAB2 equivalencia funcional tabular bajo información igual; recableado E07 empata LRU. I3c7h discrimina refuerzo contingente, I3c7i lesión local STW, I3c7k transferencia oráculo +4.9 pp frente a +10 requerido, retención robusta 2/20 frente a 18/20. No ajustar miniC1.
- NR01: FIFO 1-NN16 S=.812083; KMeans4 .847396 (+3.53 pp frente a +5), 34% más estado, reversión .4875 frente a 1; ART excede capacidad 104/120. STOP, no confirmación.
- G05-NX01: TK=1.0 en 20 instancias, imposible mejorar .05. Brazos neuronales NO ejecutados. No es prueba general contra aprendizaje neuronal.
- G05, R-ACT-I3c, G09 no superadas. G00-H y G-H6-CLOCK abiertas. Semillas reservadas intactas. H08c.1 STOP, H08c.2/.3 no ejecutadas.
- Referencias: [cierre E09](../inherited/docs/neurolab/E09_CIERRE_FORMAL_RESULTADO_20261122.md), [reconciliación gates](../inherited/docs/neurolab/E09_00R_RECONCILIACION_GATES_20261122.md), [cierre NR01](../inherited/docs/neurolab/NR01_04_06_RESULTADO_Y_CIERRE_20261122.md), [cierre NX01](../inherited/docs/neurolab/G05_NX01_RESULTADO_Y_STOP_20261122.md). No modificar resultados anteriores.

## Evaluación de alternativas y valor marginal
A. Continuar H con un diseño multientrada/selección previa entre sujetos, nuevos controles de atención y captura completa. Podría resolver una pregunta histórica de interés, pero no hay garantía de oportunidad de aprendizaje, y supone contrato nuevo. No repetir D6 buscando topología favorable ni corregir parser para rescatar el gate. H08d acumulado: 9 jobs, 1129 s de runner, 7 arranques originales; no equivale a costo total de H. 
B. Cerrar H parcial y formular una nueva pregunta funcional N (recomendación). El mecanismo observado de borrado contextual justifica investigar qué debe desaparecer y qué conservarse, no copiar C1. Requiere aprobación explícita para reabrir N; ningún código experimental, ejecución ni reservas en este paso.
C. Detener NeuroLab si ninguna pregunta discriminante supera alternativas simples y costo marginal. Resultado legítimo. No construir arquitectura integrada por inercia.

## Hipótesis candidata N — solo propuesta, no contrato ni reapertura
¿Separar el estado transitorio de las trazas pendientes de crédito, condicionándolas a cambios de contexto observables, reduce atribuciones erróneas e interferencia sin perder recompensas válidas demoradas que cruzan esos cambios ni degradar retención activa y reversión?

Antecedentes a contrastar: [Gerstner et al. 2018, revisión de trazas de elegibilidad y reglas de tres factores](https://pmc.ncbi.nlm.nih.gov/articles/PMC6079224/); [Event boundaries shape temporal organization of memory by resetting temporal context, 2022](https://www.nature.com/articles/s41467-022-28216-9); [Dick et al. 2025, detección estadística de contexto en RL continuo](https://proceedings.mlr.press/v274/dick25a.html). No equivalen a evidencia sobre C1 ni prueban la hipótesis. Comparar soluciones existentes y reutilizables antes de desarrollo.

Primer examen documental, si aprobado:
1. Definir unidad independiente (secuencia/semilla), información común (estímulo, elección, recompensa retardada, cambio de contexto observable o inferible de esa misma corriente) y confusiones. No entregar etiquetas latentes, fuente real del premio ni retraso real privilegiados a un brazo. Incluir crédito correcto dentro y a través del cambio, distractores, inversión y evaluación activa sin recompensa.
2. Establecer identificabilidad: si dos historias observables idénticas requieren créditos incompatibles, no exigir discriminación imposible. Oráculo diagnóstico separado; comprobar margen alcanzable frente a controles simples antes de probar una red. Revisar costo informacional y computacional.
3. Contrastar trazas con decaimiento, borrado duro, trazas pendientes conservadas/segmentadas, alternativas simples (tabla con historial acotado, buffer circular, 1-NN si pertinente, detección de contexto sobre la misma señal). No favorecer lo neuronal por definición. Presupuesto comparable de estado y actualización, medir atribución, interferencia, retención activa, reversión, costo. Fijar aceptación, tamaño, stop y semillas nuevas antes de cualquier ensayo; no usar holdouts existentes.
4. Si no hay contraste identificable con valor sobre baseline simple, STOP o recomendar solución simple. Si hay fundamento, presentar contrato preregistrado al usuario; no ejecución automática.

## Conservación y auditoría
D6 código inicialmente no generado por error de interpolación; corregido antes de commit/CI, sin arranque adicional. Captura original permanece incompleta; fixture no garantiza captura integrada. Derivados compactos y recálculos verificables en repositorio; ZIP íntegros D5/D5x/D6 descargados, no archivados íntegramente aquí; cobertura histórica de archivo parcial documentada en ARCHIVE_COVERAGE.json. Sin originales, secretos ni logs sensibles publicados. Autoverificación y recálculos separados, no auditor independiente. Pausa operativa H y N STOP hasta decisión sustantiva; ninguna integración con Nilo autorizada.
