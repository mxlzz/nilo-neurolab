# Traspaso aprobado — 24/11/2026

Origen mxlzz/Nilo_public rama docs/neurolab-protocolo-20261120; corte c0c06c95c176eb9c0e0df71853313d16acda0f27. Destino mxlzz/nilo-neurolab público, inicialmente vacío. No tocar origen, PR103 ni Nilo0.7. No operar dos fuentes.

Seleccionados 514 blobs: docs/neurolab/, experiments/neurolab/, .github/workflows/neurolab-*. Preservar bajo inherited/ con estructura relativa, workflows inactivos. Verificar SHA, modo, tamaño, origen y destino; excepciones de privacidad explícitas. DAG original queda por enlace/commit, no se importa. Los enlaces históricos a raíz Nilo se resuelven en commit original; no copiar runtime ajeno. Ejecutar desde inherited/ si imports lo requieren.

Inventariar runs específicos NeuroLab, separar validación general Nilo. Archivar ZIP derivados y logs seguros recuperables, comprobar digest/CRC. No publicar EXE, GEN, ISO, DATA, DLL, recursos originales, credenciales, IDs de carpetas privadas o logs sensibles de transferencia. Metadatos y evidencia derivada H versionada sustituyen referencias a logs privados, no equivalen a su copia. Si se omite evidencia, documentar alcance y recuperación. Backups E09/NR01 en Drive quedan en canal privado, sin alterar permisos.

Secretos históricos NEUROLAB_CD_FILE_ID y NEUROLAB_DATA_FILE_ID no se transfieren automáticamente; no leer/mostrar valores, verificar disponibilidad antes de H08c.1. No volver a pedir originales si ya existen; solicitar configuración segura cuando corresponda. H08c.0 documental no depende de secretos. No activar workflows antiguos, adaptar futuros a tarea, permisos y limpieza.

M4: releer archivos y manifiestos, comparar hashes/enlaces, comprobar origen, simular continuidad y actualizar STATE al final. Si archivo de evidencia aún en curso, conservar estado de migración y registrar run. No ejecutar ciencia durante traslado.