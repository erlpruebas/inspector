# Informe ejecutivo de cuentas prioritarias

Fecha de corte: 2026-05-13

Fuentes: `assistant_synthetic/contactos_50.csv`, `assistant_synthetic/emails_hilos.md`, `assistant_synthetic/notas_voz.jsonl`.

## Resumen ejecutivo

Se identifican 23 contactos de prioridad alta en el fichero de contactos. De ellos, 8 tienen senales operativas recientes en correos o notas de voz y requieren seguimiento inmediato. Adicionalmente, hay 3 cuentas no marcadas como alta que conviene gestionar por vencimiento o impacto comercial: Delta Equipos, IberLegal y BravoSoft.

La situacion mas urgente esta en vencimientos ya superados o del dia: IberLegal pidio comentarios antes del 12 de mayo, Delta Equipos condiciona el 4% de descuento a cerrar antes del dia 13, y Clinica Centro tiene demo confirmada para el 14 de mayo a las 11:30. Tambien hay compromisos de preparacion para Barna Health, Northwind ES, Innotek, Atlantic Data, Zenit Food y Cobalto.

## Prioridad inmediata

| Cuenta | Contacto | Tipo | Prioridad | Evidencia | Riesgo | Siguiente accion |
|---|---|---:|---:|---|---|---|
| IberLegal | David Navarro, Legal | proveedor | media | Email E-003 y VN-006: respuesta contractual antes del 12 de mayo. | Alto: plazo vencido; clausula 8 de responsabilidad y renovacion automatica pueden bloquear soporte. | Enviar hoy comentarios legales concretos y pedir extension formal si falta revision interna. |
| Delta Equipos | Luis Martin, Compras | proveedor | media | Email E-002 y VN-002: 4% de descuento si se cierra antes del dia 13; falta CSV de monitores. | Alto: perdida de descuento y retraso de compra. | Enviar CSV actualizado con descuento del 4% y confirmar cierre hoy. |
| Clinica Centro | Noelia Castro, Administracion | cliente | alta | Email E-001 y VN-001/VN-019: demo de pagos el 14 de mayo a las 11:30; incluir administracion; incidencias de facturacion. | Alto: demo inminente con dependencia funcional de conciliacion/estado de pagos. | Llamar para confirmar asistentes, preparar demo de conciliacion y llevar resumen de incidencias de facturacion. |
| Barna Health | Xavier Puig, IT | cliente | alta | Email E-004 y VN-003: reunion presencial en Barcelona el 18 de mayo a las 10:00 sobre SSO. | Medio-alto: desplazamiento y agenda tecnica dependen de preparacion previa. | Comprar billete, bloquear agenda y preparar checklist de integracion SSO. |
| Innotek | Sergio Campos, CTO | cliente | alta | VN-004: preparar minuta con riesgos de seguridad y coste de auditoria. | Medio-alto: conversacion tecnica sensible por coste y seguridad. | Redactar minuta ejecutiva con riesgos, coste estimado y opciones de auditoria. |
| Atlantic Data | Elena Vidal, Finanzas | cliente | alta | VN-005: pedir facturas de abril que no aparecen en banco. | Medio-alto: conciliacion incompleta y posible tension financiera. | Solicitar facturas faltantes de abril y abrir seguimiento de conciliacion. |
| Clinica Sol | Marta Ruiz, Administracion | cliente | alta | VN-007: seguimiento el martes a las 16:00 por administracion. | Medio: reunion probablemente vencida respecto al corte; puede quedar accion sin cerrar. | Confirmar si la llamada del 12 de mayo ocurrio; si no, reagendar esta semana. |
| Nova Iberia | Ana Lopez, Directora Operaciones | cliente | alta | Email E-005 y VN-008: prefiere PDF con una pagina de resumen ejecutivo y anexos separados. | Medio: riesgo de friccion por formato si se envia material extenso o no separado. | Actualizar plantilla de entrega para Ana: PDF ejecutivo de 1 pagina mas anexos separados. |

## Cuentas altas con accion abierta

| Cuenta | Contacto | Senal detectada | Riesgo | Siguiente accion |
|---|---|---|---|---|
| Northwind ES | Laura Marin, Ventas | VN-011: enviar agenda de implantacion e incluir hito de formacion el dia 22. | Medio: implantacion sin agenda compartida o formacion no alineada. | Enviar agenda de implantacion con hito de formacion el 22 de mayo. |
| Zenit Food | Tomas Vega, Compras | VN-010: llamar por pedido de licencias y confirmar direccion fiscal. | Medio: pedido bloqueado por dato fiscal. | Llamar y registrar direccion fiscal antes de emitir documentacion. |
| Cobalto | Ivan Duran, Seguridad | VN-013: renovar certificado SSL antes del 28. | Medio: vencimiento tecnico con impacto de seguridad/servicio. | Crear tarea con fecha limite 28 de mayo y confirmar responsable tecnico. |

## Watchlist comercial y operativa

| Cuenta | Contacto | Tipo/Prioridad | Motivo | Accion recomendada |
|---|---|---:|---|---|
| BravoSoft | Paula Ferrer, Ventas | prospecto/media | Email E-006 y VN-015: propuesta CRM pendiente; si no contesta, insistir con correo corto. | Enviar correo breve de seguimiento con una pregunta de decision. |
| GreenBox | Clara Molina, Marketing | cliente/baja | VN-009: buscar alternativa barata a herramienta de encuestas. | Preparar 2-3 alternativas de bajo coste; no escalar salvo que haya presupuesto. |
| Madrid alta prioridad | Ana Lopez, Hector Mora, Raquel Cano, Ivan Duran, Noelia Castro, Samuel Ibanez, Alberto Saez, Esteban Lozano | mixto/alta | VN-017: crear lista de contactos prioritarios de Madrid. | Usar esta lista para una ronda de seguimiento semanal segmentada por ciudad. |

## Matriz de riesgos

| Riesgo | Cuentas afectadas | Severidad | Mitigacion |
|---|---|---:|---|
| Plazos vencidos o del mismo dia | IberLegal, Delta Equipos | Alta | Gestionar hoy por correo y llamada; documentar si se pierde plazo o descuento. |
| Compromisos de agenda inminentes | Clinica Centro, Barna Health, Clinica Sol | Alta | Confirmar asistentes, logistica y materiales antes de cada reunion. |
| Riesgo financiero/conciliacion | Atlantic Data, Clinica Centro | Media-alta | Recopilar facturas e incidencias; separar anexos de soporte. |
| Riesgo tecnico/seguridad | Innotek, Cobalto, Barna Health | Media-alta | Preparar minutas tecnicas y checklist con responsables y fechas. |
| Riesgo de formato/expectativas | Nova Iberia | Media | Estandarizar entregables: PDF ejecutivo breve y anexos separados. |
| Riesgo comercial por falta de seguimiento | BravoSoft, Zenit Food | Media | Mensaje corto de avance y llamada de confirmacion de datos clave. |

## Siguientes acciones recomendadas

1. Hoy, 2026-05-13: cerrar Delta Equipos o confirmar perdida/extension del descuento; enviar CSV actualizado con 4%.
2. Hoy, 2026-05-13: responder a IberLegal sobre clausula 8 y renovacion automatica; pedir extension si procede.
3. Antes del 2026-05-14 11:30: confirmar demo de Clinica Centro, asistentes de administracion y guion de conciliacion/pagos.
4. Esta semana: validar si el seguimiento con Marta Ruiz ocurrio el 12 de mayo; reagendar si quedo abierto.
5. Antes del 2026-05-18 10:00: reservar viaje a Barcelona y preparar agenda tecnica SSO para Barna Health.
6. Antes del 2026-05-22: enviar agenda de implantacion a Laura Marin con hito de formacion.
7. Antes del 2026-05-28: renovar o confirmar renovacion del certificado SSL de Cobalto.

## Observaciones de calidad de datos

- Los correos solo cubren 6 hilos, por lo que las cuentas de prioridad alta sin mencion adicional quedan como prioritarias por perfil, no por urgencia detectada.
- Las notas de voz contienen algunas tareas no vinculadas a contactos del CSV, como gastos internos o comparativas de mercado; se excluyen del nucleo del informe.
- Las fechas relativas de los correos se normalizan contra la fecha de corte 2026-05-13.
