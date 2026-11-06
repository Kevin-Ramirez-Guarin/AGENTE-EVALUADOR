# Transparencia y consentimiento en la interfaz

Cómo la interfaz informa a la persona candidata, le pide su autorización y le explica al reclutador cada resultado (PLAN §7, puntos 1, 5 y 6).

## Consentimiento (Ley 1581, art. 9)
- El formulario de aplicación tiene una casilla **no premarcada**: «Autorizo el tratamiento de mis datos (Ley 1581 de 2012)».
- Debajo explica el uso: «Usaremos tus datos solo para evaluar esta postulación. Una inteligencia artificial ayuda a analizar tu hoja de vida, pero la decisión final la toma una persona de nuestro equipo».
- Junto a la casilla hay dos enlaces: la política de privacidad y la página «Cómo evaluamos».
- Sin la casilla marcada el envío no avanza: se muestra el error y el foco pasa a la casilla. El backend también lo rechaza con 422.

## Qué ve la persona candidata y qué no
- **Ve:** la vacante, el formulario y, al enviar, «Recibimos tu postulación». El mensaje es el mismo mientras la evaluación corre en segundo plano.
- **No ve nunca:** el puntaje, el veredicto sugerido ni el perfil extraído. Solo recibe el correo que el reclutador aprueba.

## Página «Cómo evaluamos» (`/como-evaluamos`)
Está escrita en lenguaje claro y explica:
- Los 5 criterios con su peso: los de la vacante si llega `?vacante=`, o los genéricos de PLAN §5 (45/25/15/10/5 %).
- Que la IA solo extrae información y sugiere, y que **una persona decide**.
- Que antes de que la IA lea la hoja de vida se quitan los datos de identificación y contacto (nombre, correo, teléfono, documento, edad, estado civil y origen) y se neutralizan las palabras que revelan el género.
- Los derechos de la Ley 1581 (conocer, actualizar, rectificar, revocar la autorización y pedir revisión humana) y cómo ejercerlos: escribir a `privacidad@nexodigital.example` (correo ficticio de Nexo Digital).

## Explicación al reclutador
- El detalle muestra, por criterio: puntaje con barra y texto, peso, requisitos cumplidos y faltantes, y la evidencia citada de la hoja de vida.
- La `nota` de cada criterio está redactada para la persona candidata («Tu experiencia…») porque se usa en el correo. En el panel se rotula «Nota para la persona candidata (se usa en el correo)», para que el reclutador entienda el tono.
- Los estados son visibles: «En evaluación» (la página se refresca sola cada 5 s), «Pendiente de revisión», «Decidida» y «Error en la evaluación» (con el motivo y el botón Reintentar).
- El formulario de decisión aparece **solo en «Pendiente de revisión»**. Si el reclutador cambia el veredicto sugerido, el motivo es obligatorio.
- Antes de registrar la decisión hay una **confirmación**: «Se enviará un correo al candidato. ¿Confirmas la decisión?». Nada sale sin esa aprobación.

## Accesibilidad
- Se prueba con `@axe-core/playwright` 4.11.2 (WCAG 2.x A y AA) en `/vacantes`, `/aplicar/:id`, `/privacidad`, `/como-evaluamos`, `/panel` y `/panel/:id` con datos.
- Resultado: **0 violaciones serias o críticas** en las 6 páginas (`e2e/accesibilidad.spec.ts`).
- Además: enlace «Saltar al contenido», etiquetas en todos los campos, errores asociados con `aria-describedby`, barras con `role="meter"` y texto, y estados que no dependen solo del color.

## Límites
- axe detecta solo una parte de los problemas; falta una prueba manual con lector de pantalla y teclado.
- No se probó axe sobre los estados «En evaluación» y «Error en la evaluación» en e2e, porque el backend de `main` aún es síncrono; se cubren con pruebas unitarias.
- El panel no tiene autenticación (aviso «Demo sin autenticación») y el reclutador se declara a sí mismo.
- «Cómo evaluamos» describe el diseño. La ausencia de sesgo se demuestra con la prueba contrafactual del backend, no con esta página.
- La neutralización del género usa una lista finita de términos: una palabra que no esté en la lista no se neutraliza.
- El correo de contacto es un canal de demostración (proyecto académico, empresa ficticia): no hay un canal real de atención de derechos, y la página lo dice explícitamente.
