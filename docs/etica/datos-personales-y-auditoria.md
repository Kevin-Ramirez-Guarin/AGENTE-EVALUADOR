# Datos personales, auditoría y retención

Este documento explica cómo el Agente Evaluador trata los datos de las personas candidatas y qué falta. Lo marcado **por verificar** no lo hemos confirmado con una fuente jurídica. Ninguna cita de artículo, decreto, circular o sentencia de este documento está confirmada por un abogado: todas son **por verificar** antes de la entrega.

## 1. Ley 1581 de 2012 (protección de datos personales)

| Principio o artículo | Cómo lo cumplimos hoy |
|---|---|
| Autorización previa, expresa e informada (art. 9, por verificar) | `POST /postulaciones` exige `consentimiento=true`; sin él responde 422 y no guarda nada. La fecha del consentimiento queda en `Postulacion.consentimiento_at` y en la auditoría. El formulario enlaza a la política de tratamiento (el texto de la política está **por verificar**). |
| Finalidad (principio del art. 4 lit. b, por verificar; el art. 12, por verificar, es el deber de informar la finalidad al titular) | Los datos se usan solo para evaluar la postulación a la vacante y, si el reclutador decide, para contactar a la persona (correo y entrevista). No se reutilizan para otras finalidades. |
| Datos sensibles (art. 5, por verificar) | No se piden. El agente tiene la instrucción de no extraer género, edad, origen ni estado civil, y el nombre y el contacto se guardan aparte de la HV. La anonimización antes del LLM la implementa el track IA (Sprint 3) y no forma parte de esta rama. |
| Calidad, seguridad y circulación restringida | Ver secciones 5 y 6. |

**Derechos del titular y cómo se atienden hoy**

| Derecho | Atención actual |
|---|---|
| Conocer | No hay endpoint para el titular. El reclutador ve el detalle explicado (`GET /evaluaciones/{id}`) y la persona recibe un correo con las razones. Una solicitud se atiende a mano consultando la BD. |
| Actualizar y rectificar | Proceso manual: el responsable edita `Candidato` en la BD. No hay endpoint. |
| Revocar la autorización / suprimir | Proceso manual: se ejecuta la purga de esa postulación (ver sección 5). No hay endpoint ni identidad verificada del solicitante. |
| Quejas ante la SIC | Se informa en la política de tratamiento (**por verificar** que el texto esté publicado). |

Esto es deuda reconocida: los derechos existen en el papel y se atienden por proceso humano, no por una función del sistema.

## 2. Decreto 1377 de 2013 (compilado en el Decreto 1074 de 2015) (por verificar)
Reglamenta la autorización y la política de tratamiento. Aplicamos: autorización por un medio verificable (casilla más fecha guardada), informar la finalidad y conservar prueba de la autorización. **Por verificar:** el contenido mínimo exacto de la política de tratamiento y si corresponde inscribir la base de datos en el RNBD.

## 3. Circular Externa 002 de 2024 de la SIC (IA y datos personales)
Pide que el tratamiento con IA sea necesario, idóneo y proporcional, y una evaluación de impacto de privacidad previa. **Por verificar:** el texto exacto y su alcance.

- **Necesidad e idoneidad:** solo se procesa la HV que la persona envía, para puntuar contra requisitos de la vacante.
- **Proporcionalidad:** con el anonimizador integrado (track IA, Sprint 3), el LLM no recibiría nombre ni contacto; esta rama no lo garantiza por sí sola. La IA solo sugiere y un humano decide (`decision` exige reclutador y, si contradice a la IA, un motivo).
- **Evaluación de impacto de privacidad:** se redacta en el informe final (PLAN §7.8); aún no está terminada.

## 4. Sentencia T-323 de 2024
La referenciamos por su relación con decisiones automatizadas y la intervención humana. **Por verificar** su contenido exacto antes de citarla. En el diseño: la IA nunca rechaza sola, hay explicación por criterio con evidencias y se audita la decisión humana.

## 5. Auditoría, retención y seguridad

**Auditoría** (tabla `Auditoria`, sin PDF ni datos de contacto en el detalle): `postulacion_rechazada`, `evaluacion_creada`, `evaluacion_fallida`, `decision` (veredicto de la IA y final, motivo y reclutador), `notificacion_enviada`, `notificacion_omitida`, `notificacion_fallida` y `datos_purgados`.

**Retención:** `python -m scripts.purgar_datos --dias 180 [--dry-run]` (desde `backend/`). Para las postulaciones con más de 180 días borra el PDF, reemplaza nombre y correo por `[eliminado]` y audita `datos_purgados`. También vacía el perfil y, del resultado, elimina el resumen, las evidencias, las notas, las fortalezas y las debilidades; conserva solo `puntaje_total`, los puntajes por criterio y los veredictos (sugerido y final), junto con el reclutador y el motivo de la decisión. Esa evidencia de que hubo un humano en el bucle ya no contiene texto de la HV. El motivo que escribe el reclutador es texto libre y podría contener datos personales: no se redacta. Solo se purgan evaluaciones `pendiente_revision` o `decidida`; las `en_evaluacion` y `error_evaluacion` conservan su PDF hasta resolverse (deuda: una en error permanente no se purga). Hoy se ejecuta a mano o con el programador de tareas del sistema; no corre solo. El plazo de 6 meses es una decisión del proyecto: su suficiencia legal está **por verificar**.

**Seguridad:** validación en la frontera (consentimiento, tipo, magic bytes, máx. 5 MB, formato de correo, texto legible); PDFs guardados con nombre UUID (sin ruta del cliente); `token.json` de Google con permisos 0o600; `.env`, `credentials*.json` y `token*.json` en `.gitignore`, sin secretos en el repo.

## 6. Deuda honesta
- **Sin autenticación:** cualquiera que alcance la API puede listar evaluaciones, ver datos de candidatos y decidir.
- **`reclutador` lo declara el cliente:** la auditoría registra un nombre que no está verificado, así que no prueba quién decidió.
- Sin endpoints para los derechos del titular; la purga no es automática; las BD y los PDF no están cifrados en reposo.
- La política de tratamiento, el RNBD y la evaluación de impacto siguen pendientes o por verificar.
