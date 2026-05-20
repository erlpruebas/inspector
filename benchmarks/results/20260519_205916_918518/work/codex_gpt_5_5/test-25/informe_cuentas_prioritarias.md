# Informe ejecutivo de cuentas prioritarias

Fecha de corte: 20 de mayo de 2026  
Fuentes: `assistant_synthetic/contactos_50.csv`, `assistant_synthetic/emails_hilos.md`, `assistant_synthetic/notas_voz.jsonl`

## Resumen ejecutivo

Se identifican 10 cuentas con senales accionables inmediatas. La mayor concentracion de riesgo esta en plazos ya vencidos o muy cercanos: revision contractual de IberLegal, descuento de monitores condicionado al cierre antes del dia 13, visita tecnica de Barna Health del dia 18, seguimiento de demo de pagos en ORG_0005 y renovacion SSL de Cobalto antes del dia 28.

Prioridad recomendada para las proximas 48 horas:

1. Cerrar pendientes vencidos: IberLegal, descuento monitores de PERSON_0065 y demo de pagos de ORG_0005.
2. Confirmar estado post-reunion de Barna Health y documentar decisiones sobre SSO.
3. Preparar entregables especificos para PERSON_0068 e Innotek, ajustados a las preferencias y riesgos mencionados.
4. Asegurar hitos operativos de Northwind ES y Cobalto antes de que se conviertan en incidencias.

## Cuentas prioritarias

| Cuenta | Contacto principal | Tipo / prioridad | Senales combinadas | Riesgos | Siguientes acciones |
|---|---|---:|---|---|---|
| ORG_0005 | PERSON_0001, Administracion, Madrid | Cliente / alta | Solicita demo de modulo de pagos; nota pide llamar a Noelia antes del jueves para confirmar el modulo de pagos. | Riesgo comercial por falta de confirmacion y posible perdida de impulso en una oportunidad activa. | Llamar a Noelia hoy; confirmar asistentes de administracion; enviar agenda de demo centrada en conciliacion y estado de pagos; registrar decision y proximo hito. |
| PERSON_0068 | PERSON_0069, rol PERSON_0067, Madrid | Cliente / alta | Solicita informes siempre en PDF, con una pagina de resumen ejecutivo y anexos separados; la nota de voz refuerza esta preferencia. | Riesgo de friccion ejecutiva si se envia un formato incorrecto o demasiado largo. | Estandarizar plantilla PDF de una pagina para esta cuenta; separar anexos; usar este informe como formato base para futuras entregas. |
| Clinica Sol | PERSON_0064, Administracion, Sevilla | Cliente / alta | Nota: agendar seguimiento con PERSON_0064 el martes a las cuatro por tema de administracion. | Riesgo operativo por tema administrativo abierto sin detalle; posible bloqueo de facturacion, acceso o documentacion. | Confirmar si la reunion ya ocurrio; pedir contexto del problema administrativo; preparar checklist de documentos o decisiones necesarias. |
| Innotek | PERSON_0060, CTO, Zaragoza | Cliente / alta | Nota: preparar minuta con riesgos de seguridad y coste de auditoria. | Riesgo tecnico y presupuestario; puede afectar aprobacion o continuidad si no se cuantifica. | Preparar minuta ejecutiva con matriz de riesgos, coste estimado de auditoria, alcance minimo viable y decision requerida del CTO. |
| IberLegal | PERSON_0058, Legal, Madrid | Proveedor / media | Solicita comentarios antes del 12 de mayo; preocupan clausula 8 de responsabilidad y renovacion automatica; nota pide crear tarea de revision. | Plazo vencido; riesgo contractual por responsabilidad y renovacion automatica no negociada. | Responder hoy con comentarios preliminares; marcar clausula 8 y renovacion como puntos no aceptados sin revision; proponer redline y llamada legal. |
| Barna Health | PERSON_0024, IT, Barcelona | Cliente / alta | Reunion presencial en Barcelona el 18 de mayo para integracion SSO; nota condiciona comprar billete si Xavier confirma. | La fecha de reunion ya paso; riesgo de no capturar acuerdos tecnicos o de viaje/agenda descoordinada. | Confirmar si la reunion se celebro; documentar decisiones SSO, responsables y bloqueos; enviar acta y plan tecnico de integracion. |
| BravoSoft | PERSON_0059, Ventas, Malaga | Prospecto / media | Propuesta CRM pendiente; contacto pide insistir con correo corto si no contesta; nota confirma falta de respuesta. | Riesgo de enfriamiento de oportunidad comercial. | Enviar correo breve de seguimiento con una sola pregunta de avance; ofrecer dos ventanas de llamada; actualizar probabilidad de cierre. |
| PERSON_0065 | PERSON_0066, Compras, Valencia | Proveedor / media | Oferta de monitores con 4% de descuento si se cerraba antes del dia 13; nota pide enviar CSV actualizado con el descuento. | Plazo de descuento vencido; riesgo de coste adicional o datos de compra incorrectos. | Confirmar si el 4% sigue vigente; enviar CSV corregido; pedir extension formal del descuento si la compra sigue abierta. |
| Cobalto | PERSON_0037, Seguridad, Madrid | Proveedor / alta | Nota: renovar certificado SSL antes del 28. | Riesgo critico de interrupcion o alerta de seguridad si vence el certificado. | Validar fecha exacta de caducidad; asignar responsable; renovar y probar certificado antes del 28 de mayo; guardar evidencia. |
| Northwind ES | PERSON_0033, Ventas, Bilbao | Cliente / alta | Nota: enviar agenda de implantacion e incluir hito de formacion el dia 22. | Riesgo de implantacion por falta de agenda y formacion no calendarizada. | Enviar agenda de implantacion hoy; bloquear hito de formacion del 22; confirmar asistentes y materiales. |

## Riesgos transversales

- Fechas vencidas: 12, 13 y 18 de mayo aparecen asociadas a contrato, descuento y visita tecnica. Requieren cierre de estado, no solo nueva tarea.
- Preferencias de entregables: PERSON_0068 exige PDF con resumen ejecutivo y anexos separados. Esta preferencia debe aplicarse en toda comunicacion ejecutiva con esa cuenta.
- Riesgo operativo-documental: aparecen facturas, banco, direccion fiscal y administracion en notas no siempre vinculadas a una cuenta con claridad. Conviene crear una cola de conciliacion y datos fiscales.
- Dependencia de contactos anonimizados: algunas notas mencionan PERSON_0072, PERSON_0073, PERSON_0074, ORG_0007 y ORG_0008 sin correspondencia directa en `contactos_50.csv`. Deben resolverse antes de asignar propietario.

## Acciones inmediatas recomendadas

1. Hoy: enviar respuestas de desbloqueo a IberLegal, BravoSoft, ORG_0005, PERSON_0065 y Northwind ES.
2. En 24 horas: cerrar acta de Barna Health, preparar minuta de Innotek y confirmar seguimiento con Clinica Sol.
3. Antes del 28 de mayo: renovar y verificar SSL de Cobalto.
4. Esta semana: depurar entidades sin correspondencia en contactos y crear tareas separadas para facturas, direccion fiscal y conciliacion bancaria.

## Datos por resolver

- PERSON_0072: pedido de licencias y direccion fiscal.
- PERSON_0073: facturas de abril no localizadas en banco.
- PERSON_0074: destinatario del CSV actualizado de monitores.
- ORG_0007: incidencia de facturacion para informe mensual.
- ORG_0008: posible factura faltante de 847,50.
