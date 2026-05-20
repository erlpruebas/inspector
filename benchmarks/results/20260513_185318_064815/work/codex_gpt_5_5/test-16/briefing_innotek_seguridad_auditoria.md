# Briefing de seguridad y auditoria para Innotek

Destinatario: Sergio Campos, CTO de Innotek  
Contacto: sergio.campos@innotek.es, +34 600 100 006  
Prioridad: alta  
Fecha de preparacion: 2026-05-13

## Objetivo

Preparar una conversacion ejecutiva con Sergio Campos sobre riesgos de seguridad, controles de auditoria y coste orientativo de una revision inicial. La base de este briefing son los recursos locales `assistant_synthetic/notas_voz.jsonl` y `assistant_synthetic/contactos_50.csv`.

## Contexto relevante

- Sergio Campos aparece como CTO de Innotek, cliente de prioridad alta.
- La nota VN-004 pide explicitamente preparar una minuta para Sergio Campos sobre riesgos de seguridad y coste de auditoria.
- Hay senales operativas relacionadas con pagos, facturas, CSVs, licencias, direccion fiscal, certificados SSL e incidencias de facturacion.
- La cartera local contiene 50 contactos: 30 clientes, 8 proveedores, 6 partners y 6 prospectos. De ellos, 23 son de prioridad alta.

## Riesgos principales

1. Gestion de datos y ficheros compartidos

   Evidencia local: VN-002 menciona el envio de un CSV actualizado de monitores a un proveedor. Esto sugiere intercambio de ficheros operativos con terceros.

   Riesgo: fuga de informacion, envio al destinatario incorrecto, versiones no controladas, ausencia de cifrado o trazabilidad.

   Recomendacion: definir clasificacion de datos, canal aprobado de intercambio, control de permisos, caducidad de enlaces y registro de envios.

2. Pagos, facturacion y conciliacion

   Evidencia local: VN-001 menciona demo de modulo de pagos; VN-005 facturas que no aparecen en el banco; VN-012 cargos duplicados; VN-016 cruce de pagos con facturas; VN-019 incidencias con facturacion.

   Riesgo: errores de conciliacion, fraude de factura, pagos duplicados, falta de segregacion de funciones y debilidad en trazabilidad contable.

   Recomendacion: revisar circuito de aprobacion de pagos, conciliacion bancaria, controles antifraude, evidencias de autorizacion y logs de cambios en facturas.

3. Certificados y continuidad de servicio

   Evidencia local: VN-013 pide renovar un certificado SSL de Cobalto antes del dia 28.

   Riesgo: caducidad de certificados, caida de servicios, errores de integracion, degradacion de confianza y exposicion a incidentes por configuracion TLS debil.

   Recomendacion: inventario de certificados, alertas con 30/15/7 dias de antelacion, responsable asignado y verificacion de configuracion TLS.

4. Terceros, contratos y licencias

   Evidencia local: VN-006 habla de revision de contrato con IberLegal; VN-010 menciona pedido de licencias y direccion fiscal; el CSV local incluye proveedores, partners y clientes prioritarios.

   Riesgo: dependencias sin clausulas de seguridad suficientes, licencias no inventariadas, exposicion de datos fiscales y falta de control sobre accesos de terceros.

   Recomendacion: matriz de terceros criticos, revision de clausulas de confidencialidad, tratamiento de datos, derecho de auditoria, SLA de incidentes y proceso de alta/baja de accesos.

5. Incidencias y gobierno operativo

   Evidencia local: VN-019 pide informe mensual de incidencias e incluir Clinica Centro y facturacion.

   Riesgo: gestion reactiva de incidencias, baja trazabilidad, falta de metricas, decisiones sin evidencia y dificultad para demostrar cumplimiento en auditoria.

   Recomendacion: registro unico de incidencias, severidad, propietario, causa raiz, acciones correctivas, tiempos de resolucion y resumen mensual para direccion.

## Propuesta de auditoria inicial

Alcance recomendado para una primera fase:

- Revision de accesos y permisos en sistemas criticos.
- Revision del flujo de pagos, facturacion y conciliacion.
- Inventario de certificados, dominios, licencias y terceros criticos.
- Muestreo de evidencias: contratos, logs, aprobaciones, incidencias y ficheros compartidos.
- Entrevistas breves con CTO, administracion/finanzas y responsable de operaciones.
- Informe final con mapa de riesgos, prioridades, quick wins y plan de remediacion a 30/60/90 dias.

Estimacion orientativa de esfuerzo:

- Diagnostico rapido: 3 a 5 jornadas.
- Auditoria inicial razonable: 7 a 10 jornadas.
- Auditoria ampliada con terceros y evidencias tecnicas: 12 a 18 jornadas.

Nota: los archivos locales no incluyen tarifa dia ni presupuesto cerrado. Conviene presentar el coste como rango pendiente de confirmar tras definir sistemas, numero de usuarios, proveedores y evidencias disponibles.

## Mensaje sugerido para Sergio

Sergio, he preparado una revision inicial centrada en riesgos practicos: intercambio de ficheros, pagos y facturacion, certificados, terceros y gestion de incidencias. La recomendacion es empezar con una auditoria acotada de 7 a 10 jornadas para obtener un mapa claro de riesgos, controles existentes y acciones prioritarias. Si el alcance incluye terceros, evidencias tecnicas profundas o revision contractual completa, lo razonable es ampliar a 12 a 18 jornadas.

## Preguntas para cerrar alcance

- Que sistemas soportan pagos, facturacion y conciliacion?
- Quien aprueba pagos y quien puede modificar datos bancarios o fiscales?
- Como se comparten CSVs, informes y datos con proveedores o clientes?
- Hay inventario de certificados, dominios, licencias y responsables?
- Que proveedores tienen acceso a datos o sistemas de Innotek?
- Existe registro formal de incidencias y acciones correctivas?

## Prioridades inmediatas

1. Confirmar alcance de auditoria con Sergio Campos.
2. Pedir inventario de sistemas, proveedores, certificados y licencias.
3. Revisar controles de pagos/facturacion antes de entrar en controles menos criticos.
4. Preparar lista de evidencias solicitadas para evitar una auditoria basada solo en entrevistas.
5. Acordar formato de informe ejecutivo y plan de remediacion.
