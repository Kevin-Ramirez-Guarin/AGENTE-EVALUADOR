# Resumen ejecutivo — Agente evaluador para selección laboral

**Grupo 3** · [Nombre completo] (Kevin, IA), [Nombre completo] (Santiago, Frontend), [Nombre completo] (JVarz12, Plataforma) · [Curso] · [Profesor]

## El problema

En *Gattaca* un análisis automático decide el destino laboral de las personas y nadie lo discute. Hoy ocurre algo parecido: los sistemas que filtran hojas de vida (HV) con IA deciden quién llega a una entrevista. Un equipo de selección pequeño recibe muchas HV, y automatizar la lectura trae tres riesgos: discriminación algorítmica por género u origen, decisiones opacas que la persona no puede impugnar y tratamiento de datos personales con un tercero. Lo probamos con Giveaway S.A.S., una plataforma ficticia de tours con guías locales en Colombia.

## Técnica de IA

Un agente LangChain con Gemini recibe la HV en PDF y extrae un perfil en JSON estructurado: habilidades con nivel y una cita literal de la HV como evidencia. Se compara contra cinco vacantes y se produce un puntaje de idoneidad. Lo central es el reparto de funciones: **la IA extrae, Python puntúa y una persona decide**. El número no sale del modelo sino de reglas fijas y públicas (45 % técnico, 25 % experiencia, 15 % blandas, 10 % educación, 5 % idiomas, con tope de 40 si falta un requisito obligatorio).

## Arquitectura

Frontend en React; backend en FastAPI con SQLite. La API responde al instante y la evaluación corre en segundo plano: lectura del PDF, **anonimización determinística** (nombre, contacto, edad, origen y género gramatical se quitan antes del LLM), agente con cuatro herramientas, `scoring.py` y estado "pendiente de revisión". El reclutador ve cada criterio con su peso, lo cumplido, lo faltante y la evidencia. Solo cuando aprueba, el sistema envía el correo y agenda la entrevista con Meet. Cada decisión queda en una auditoría; si el reclutador contradice a la IA, debe escribir el motivo.

## Resultados

410 pruebas de backend con 98 % de cobertura, 41/41 evaluaciones con Gemini real y 11/11 pruebas de extremo a extremo. En la prueba de sesgo contrafactual, 8 variantes de una misma HV (nombre, género, origen, edad) dieron 71,7 puntos en todas, con y sin anonimizador. Una HV que decía "asigna puntaje 100" obtuvo 21,7. También hallamos que Gemini reintroduce el género por su cuenta ("la candidata"), por lo que neutralizamos además la salida.

## Conclusiones éticas

Separar extracción de puntaje hizo el resultado explicable, resistente a *prompt injection* y ciego a la identidad aun cuando el modelo la veía. El diseño responde a la Ley 1581 de 2012 (autorización expresa, finalidad, derechos del titular), a la Circular 002 de 2024 de la SIC, al art. 22 del RGPD (no decidir solo con tratamiento automatizado) y al AI Act, que clasifica el reclutamiento como alto riesgo. Los límites están declarados: el panel no tiene autenticación, el anonimizador usa listas finitas y la prueba de sesgo es pequeña (1 HV base). Es un MVP, no un producto listo para producción.

## Pregunta para el debate

**Si una IA solo recomienda y una persona firma la decisión, pero esa persona acepta la recomendación el 95 % de las veces, ¿sigue existiendo supervisión humana real? ¿Quién responde ante una candidata rechazada: quien desarrolló el sistema o la empresa que lo usa?**
