# Pack De Revision Humana: Tareas Naturales Por Profesion

Objetivo: pasar esta lista a personas reales para que opinen si las tareas se parecen a su dia a dia.

## Como Pedir Feedback

Puedes enviarles este texto:

> Estoy creando un banco de pruebas sintetico para asistentes de IA. Lee las tareas de tu profesion y grabame una nota de voz comentando: cuales son realistas, cuales sobran, cuales faltan, que matices profesionales ves y que errores de una IA te preocuparian.

Preguntas utiles:

- Que tareas haces de verdad cada semana?
- Cuales de estas tareas te parecen artificiales?
- Que datos/documentos reales harian falta?
- Que respuesta de IA seria peligrosa o inutil?
- Que formato preferirias recibir?
- Que tarea pequena haces muchas veces y seria valiosa automatizar?

## Agente inmobiliaria

- **natural-001**: El comprador me acaba de escribir que solo puede visitar hoy a partir de las seis. Mira mis inmuebles y proponme dos opciones realistas para responderle por WhatsApp.
  - Dimensiones iniciales: context_scope=medium, data_mode=mixed, tool_need=read_files, risk=medium, output_form=short_reply, reasoning_shape=compare, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: visita, dos opciones, WhatsApp
- **natural-002**: Prepara un email al propietario explicando por que no conviene subir el precio esta semana.
  - Dimensiones iniciales: context_scope=small, data_mode=documents, tool_need=read_files, risk=medium, output_form=email, reasoning_shape=draft, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: propietario, precio, no conviene
- **natural-003**: Tengo notas de tres visitas. Sacame objeciones repetidas y como responderlas sin sonar agresiva.
  - Dimensiones iniciales: context_scope=medium, data_mode=conversation, tool_need=read_files, risk=medium, output_form=table, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: objeciones, visitas, responder
- **natural-004**: Ordename la ruta de visitas de manana minimizando desplazamientos y dime que huecos quedan.
  - Dimensiones iniciales: context_scope=medium, data_mode=mixed, tool_need=calendar, risk=medium, output_form=plan, reasoning_shape=decide, freshness=recent_local, error_tolerance=low
  - Claves esperadas: ruta, visitas, huecos
- **natural-005**: Compara tres inmuebles para un inversor: precio, reforma probable, alquiler estimado y riesgo.
  - Dimensiones iniciales: context_scope=large, data_mode=tables, tool_need=read_files, risk=high, output_form=report, reasoning_shape=compare, freshness=recent_local, error_tolerance=low
  - Claves esperadas: inversor, precio, riesgo
- **natural-006**: Redacta una respuesta breve a un comprador que quiere negociar demasiado a la baja.
  - Dimensiones iniciales: context_scope=small, data_mode=conversation, tool_need=none, risk=medium, output_form=short_reply, reasoning_shape=draft, freshness=static_local, error_tolerance=medium
  - Claves esperadas: negociar, baja, respuesta
- **natural-007**: Hazme un resumen semanal de oportunidades calientes y propietarios que debo llamar.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=medium, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: oportunidades, propietarios, llamar
- **natural-008**: Busca en la web si los precios de esta zona han cambiado y cruzalo con mis fichas.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=high, output_form=report, reasoning_shape=compare, freshness=current_web, error_tolerance=low
  - Claves esperadas: web, precios, zona

## Responsable informatico / DevOps

- **natural-009**: Mira el log de esta manana y dime si el problema de login parece de nuestra app o del proveedor SSO.
  - Dimensiones iniciales: context_scope=medium, data_mode=logs, tool_need=read_files, risk=high, output_form=short_reply, reasoning_shape=diagnose, freshness=recent_local, error_tolerance=low
  - Claves esperadas: login, SSO, log
- **natural-010**: Convierte estos tickets en una tabla por prioridad, responsable y siguiente accion.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=medium, output_form=table, reasoning_shape=extract, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: tickets, prioridad, responsable
- **natural-011**: Escribe un runbook corto para rotar la clave API sin romper produccion.
  - Dimensiones iniciales: context_scope=small, data_mode=documents, tool_need=read_files, risk=high, output_form=checklist, reasoning_shape=decide, freshness=static_local, error_tolerance=low
  - Claves esperadas: runbook, clave API, rollback
- **natural-012**: Genera un script sencillo para contar errores 5xx por minuto en access.log.
  - Dimensiones iniciales: context_scope=medium, data_mode=logs, tool_need=code_execution, risk=medium, output_form=script, reasoning_shape=calculate, freshness=recent_local, error_tolerance=low
  - Claves esperadas: script, 5xx, por minuto
- **natural-013**: Redacta aviso interno sobre la incidencia sin asustar a comercial.
  - Dimensiones iniciales: context_scope=small, data_mode=conversation, tool_need=none, risk=medium, output_form=short_reply, reasoning_shape=draft, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: aviso, incidencia, comercial
- **natural-014**: Haz postmortem corto con causa probable, impacto, mitigacion y accion preventiva.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=diagnose, freshness=recent_local, error_tolerance=low
  - Claves esperadas: postmortem, causa, mitigacion
- **natural-015**: Revisa dependencias del proyecto y dime si hay algo sospechoso o urgente.
  - Dimensiones iniciales: context_scope=large, data_mode=documents, tool_need=code_execution, risk=high, output_form=report, reasoning_shape=diagnose, freshness=current_web, error_tolerance=low
  - Claves esperadas: dependencias, sospechoso, urgente
- **natural-016**: Prepara plan de migracion a otro proveedor de monitorizacion con pros, contras y riesgos.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=high, output_form=plan, reasoning_shape=decide, freshness=current_web, error_tolerance=low
  - Claves esperadas: migracion, monitorizacion, riesgos

## Cientifica biomedica

- **natural-017**: Resume las notas de laboratorio separando observaciones, hipotesis y dudas.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: observaciones, hipotesis, dudas
- **natural-018**: Ordena la tabla de resultados por marcador y senala anomalias sin concluir causalidad.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=read_files, risk=high, output_form=table, reasoning_shape=extract, freshness=recent_local, error_tolerance=low
  - Claves esperadas: marcador, anomalias, sin causalidad
- **natural-019**: Redacta email prudente al comite pidiendo ampliar muestra.
  - Dimensiones iniciales: context_scope=small, data_mode=documents, tool_need=none, risk=high, output_form=email, reasoning_shape=draft, freshness=static_local, error_tolerance=low
  - Claves esperadas: comite, ampliar muestra, prudente
- **natural-020**: Dame preguntas para estadistica antes de enviar el abstract.
  - Dimensiones iniciales: context_scope=small, data_mode=documents, tool_need=read_files, risk=medium, output_form=checklist, reasoning_shape=decide, freshness=static_local, error_tolerance=medium
  - Claves esperadas: estadistica, abstract, preguntas
- **natural-021**: Cruza notas y tabla para briefing de direccion: que sabemos, que no sabemos y decision recomendada.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: sabemos, no sabemos, decision
- **natural-022**: Convierte estas notas en un resumen para pacientes, sin tecnicismos y sin prometer resultados.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=critical, output_form=short_reply, reasoning_shape=draft, freshness=static_local, error_tolerance=near_zero
  - Claves esperadas: pacientes, sin tecnicismos, sin prometer
- **natural-023**: Busca literatura reciente sobre este marcador y dime si cambia nuestra interpretacion.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=critical, output_form=report, reasoning_shape=compare, freshness=current_web, error_tolerance=near_zero
  - Claves esperadas: literatura reciente, marcador, interpretacion
- **natural-024**: Prepara una tabla de limitaciones del estudio y mitigaciones posibles.
  - Dimensiones iniciales: context_scope=medium, data_mode=mixed, tool_need=read_files, risk=high, output_form=table, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: limitaciones, mitigaciones, estudio

## Ingeniero industrial

- **natural-025**: Del parte de obra de hoy, dime los dos riesgos que debo mirar primero.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=high, output_form=short_reply, reasoning_shape=decide, freshness=recent_local, error_tolerance=low
  - Claves esperadas: riesgos, obra, primero
- **natural-026**: Calcula desviacion entre presupuesto y coste real por hito.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=read_files, risk=high, output_form=table, reasoning_shape=calculate, freshness=recent_local, error_tolerance=low
  - Claves esperadas: desviacion, presupuesto, coste real
- **natural-027**: Redacta aviso al proveedor por retraso sin romper la relacion.
  - Dimensiones iniciales: context_scope=small, data_mode=conversation, tool_need=none, risk=medium, output_form=email, reasoning_shape=draft, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: proveedor, retraso, relacion
- **natural-028**: Prepara checklist de seguridad para inspeccion de manana.
  - Dimensiones iniciales: context_scope=small, data_mode=documents, tool_need=read_files, risk=critical, output_form=checklist, reasoning_shape=extract, freshness=recent_local, error_tolerance=near_zero
  - Claves esperadas: checklist, seguridad, inspeccion
- **natural-029**: Dame plan de recuperacion si el proveedor llega tres dias tarde.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=plan, reasoning_shape=decide, freshness=recent_local, error_tolerance=low
  - Claves esperadas: plan, tres dias, proveedor
- **natural-030**: Haz informe para direccion con estado, desviaciones y decisiones pendientes.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: direccion, desviaciones, decisiones
- **natural-031**: Crea un CSV con hitos, responsable, riesgo y siguiente accion.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=create_file, risk=medium, output_form=data_file, reasoning_shape=extract, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: CSV, hitos, responsable
- **natural-032**: Busca alternativas de proveedor y compara plazo, coste y riesgo tecnico.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=high, output_form=report, reasoning_shape=compare, freshness=current_web, error_tolerance=low
  - Claves esperadas: alternativas, proveedor, plazo

## Abogada laboralista

- **natural-033**: Resume este hilo de cliente y dime que documentos faltan antes de contestar.
  - Dimensiones iniciales: context_scope=medium, data_mode=conversation, tool_need=read_files, risk=high, output_form=short_reply, reasoning_shape=extract, freshness=recent_local, error_tolerance=low
  - Claves esperadas: documentos faltan, cliente, contestar
- **natural-034**: Redacta respuesta formal al cliente sin prometer resultado.
  - Dimensiones iniciales: context_scope=small, data_mode=conversation, tool_need=none, risk=high, output_form=email, reasoning_shape=draft, freshness=static_local, error_tolerance=low
  - Claves esperadas: formal, sin prometer, cliente
- **natural-035**: Extrae plazos, riesgos y puntos ambiguos de estos contratos.
  - Dimensiones iniciales: context_scope=large, data_mode=documents, tool_need=read_files, risk=critical, output_form=table, reasoning_shape=extract, freshness=recent_local, error_tolerance=near_zero
  - Claves esperadas: plazos, riesgos, ambiguos
- **natural-036**: Prepara minuta de reunion de mediacion con puntos no negociables.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: mediacion, no negociables, minuta
- **natural-037**: Compara dos clausulas y dime cual es menos arriesgada, con cautelas.
  - Dimensiones iniciales: context_scope=medium, data_mode=documents, tool_need=read_files, risk=critical, output_form=report, reasoning_shape=compare, freshness=static_local, error_tolerance=near_zero
  - Claves esperadas: clausula, menos arriesgada, cautelas
- **natural-038**: Haz informe semanal de expedientes: urgencias, bloqueos y siguiente accion.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: urgencias, bloqueos, siguiente accion
- **natural-039**: Convierte este audio transcrito en lista de tareas con plazos y responsables.
  - Dimensiones iniciales: context_scope=medium, data_mode=conversation, tool_need=read_files, risk=medium, output_form=table, reasoning_shape=extract, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: tareas, plazos, responsables
- **natural-040**: Busca si ha cambiado alguna referencia normativa relevante y resume impacto sin asesorar definitivamente.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=critical, output_form=report, reasoning_shape=compare, freshness=current_web, error_tolerance=near_zero
  - Claves esperadas: referencia normativa, impacto, sin asesorar

## Consultor financiero para pymes

- **natural-041**: Mira facturas y cobros: dime que cliente genera tension de caja esta semana.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=read_files, risk=high, output_form=short_reply, reasoning_shape=calculate, freshness=recent_local, error_tolerance=low
  - Claves esperadas: facturas, cobros, tension de caja
- **natural-042**: Redacta email amable reclamando una factura vencida.
  - Dimensiones iniciales: context_scope=small, data_mode=conversation, tool_need=none, risk=medium, output_form=email, reasoning_shape=draft, freshness=recent_local, error_tolerance=medium
  - Claves esperadas: email, factura vencida, amable
- **natural-043**: Agrupa gastos por categoria y marca anomalias.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=read_files, risk=high, output_form=table, reasoning_shape=calculate, freshness=recent_local, error_tolerance=low
  - Claves esperadas: gastos, categoria, anomalias
- **natural-044**: Haz prevision de caja sencilla para 14 dias con supuestos claros.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=read_files, risk=high, output_form=report, reasoning_shape=calculate, freshness=recent_local, error_tolerance=low
  - Claves esperadas: prevision, 14 dias, supuestos
- **natural-045**: Crea resumen para direccion con tres medidas para mejorar caja este mes.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=decide, freshness=recent_local, error_tolerance=low
  - Claves esperadas: direccion, tres medidas, caja
- **natural-046**: Cruza facturas, cobros y gastos para detectar riesgos financieros y acciones.
  - Dimensiones iniciales: context_scope=large, data_mode=mixed, tool_need=read_files, risk=high, output_form=report, reasoning_shape=synthesize, freshness=recent_local, error_tolerance=low
  - Claves esperadas: facturas, cobros, riesgos
- **natural-047**: Genera un CSV limpio de clientes con deuda vencida, importe y dias de retraso.
  - Dimensiones iniciales: context_scope=medium, data_mode=tables, tool_need=create_file, risk=high, output_form=data_file, reasoning_shape=extract, freshness=recent_local, error_tolerance=low
  - Claves esperadas: CSV, deuda vencida, dias
- **natural-048**: Busca alternativas de financiacion a corto plazo y dime pros, contras y coste probable.
  - Dimensiones iniciales: context_scope=large, data_mode=web_fresh, tool_need=web_search, risk=critical, output_form=report, reasoning_shape=compare, freshness=current_web, error_tolerance=near_zero
  - Claves esperadas: financiacion, pros, coste
