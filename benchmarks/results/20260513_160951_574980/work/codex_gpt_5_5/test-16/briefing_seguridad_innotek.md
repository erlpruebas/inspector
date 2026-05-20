# Briefing de seguridad y auditoria para Sergio Campos - Innotek

Fecha de preparacion: 2026-05-13  
Destinatario: Sergio Campos, CTO de Innotek  
Contacto: sergio.campos@innotek.es, +34 600 100 006  
Contexto local: Sergio figura como cliente de prioridad alta en `assistant_synthetic/contactos_50.csv`. La nota `VN-004` solicita preparar una minuta sobre riesgos de seguridad y coste de auditoria.

## Resumen ejecutivo

Innotek deberia enfocar la auditoria en controles que reduzcan riesgo operativo inmediato: gestion de certificados, tratamiento de datos exportados en CSV, seguridad de pagos/facturacion, control de proveedores y revision de contratos. Las notas locales muestran varias actividades relacionadas con pagos, facturas, licencias, direccion fiscal, incidencias y renovacion de certificado SSL, por lo que el briefing debe plantearse como una auditoria practica de continuidad, datos y terceros, no solo como una revision tecnica puntual.

Prioridad recomendada: auditoria ligera inicial de 2 a 3 semanas, con inventario de activos, revision de accesos, pruebas de exposicion externa, verificacion de copias de seguridad, revision documental y plan de remediacion priorizado.

## Senales encontradas en recursos locales

- `VN-004`: peticion explicita de preparar minuta para Sergio Campos con riesgos de seguridad y coste de auditoria.
- `VN-013`: renovacion pendiente de certificado SSL de Cobalto antes del dia 28. Riesgo: caducidad de certificados, caidas de servicio o perdida de confianza en canales cifrados.
- `VN-001`: demo de modulo de pagos para Clinica Centro. Riesgo: datos sensibles o transaccionales en entornos de demo si no hay segregacion.
- `VN-002`: envio de CSV actualizado de monitores a Delta Equipos. Riesgo: exposicion de datos por adjuntos, versiones no controladas o destinatarios incorrectos.
- `VN-005`, `VN-016` y `VN-019`: facturas no localizadas, cruces de pagos e incidencias de facturacion. Riesgo: fraude, errores contables, falta de trazabilidad o controles debiles de conciliacion.
- `VN-006`: revision de contrato con IberLegal. Riesgo: clausulas insuficientes de confidencialidad, tratamiento de datos, subencargados, SLA o notificacion de incidentes.
- `VN-010`: confirmacion de direccion fiscal y pedido de licencias. Riesgo: suplantacion, cambio fraudulento de datos maestros o compras/licencias sin aprobacion.
- Contactos relevantes: Ivan Duran de Cobalto, rol Seguridad, proveedor de prioridad alta; David Navarro de IberLegal, rol Legal; Gonzalo Pardo de MintCloud, rol Cloud; Marcos Gil de Tecnoria, rol IT.

## Riesgos principales para Sergio

1. Certificados y exposicion externa

   La renovacion SSL pendiente sugiere que conviene revisar inventario de dominios, certificados, fechas de expiracion, responsables y alertas. Un certificado caducado puede interrumpir servicio, afectar integraciones y deteriorar confianza de clientes.

2. Datos en archivos y canales de envio

   La mencion al envio de CSV actualizado indica riesgo de fuga accidental, falta de cifrado, retencion excesiva o ausencia de control de versiones. Recomendacion: limitar datos exportados, usar enlaces con caducidad, registrar descargas y evitar adjuntos con datos operativos sensibles.

3. Pagos, facturacion y conciliacion

   Las notas de facturas no encontradas, cargos duplicados y cruces de pagos apuntan a necesidad de controles de auditoria: doble aprobacion para cambios bancarios, conciliacion periodica, segregacion de funciones y registro inmutable de cambios en datos maestros.

4. Proveedores y contratos

   Hay proveedores de legal, seguridad, cloud e IT en la agenda de contactos. Deben revisarse contratos, DPA, SLA, responsabilidades de seguridad, subprocesadores, plazos de notificacion de incidentes y evidencias de controles.

5. Entornos de demo y datos reales

   La demo de modulo de pagos debe ejecutarse con datos ficticios o anonimizados. Si se usan datos reales, deben aplicarse controles equivalentes a produccion: acceso minimo, trazabilidad, borrado posterior y cifrado.

6. Licencias y cambios de datos fiscales

   Confirmaciones de direccion fiscal y pedidos de licencias son vectores habituales de fraude administrativo. Recomendacion: canal verificado, aprobacion fuera de banda y registro de autorizaciones.

## Alcance recomendado de auditoria

- Inventario rapido de activos: dominios, certificados, aplicaciones, entornos, cuentas privilegiadas, proveedores criticos y flujos de datos.
- Revision de identidad y accesos: MFA, bajas de usuarios, cuentas compartidas, permisos admin y accesos de proveedores.
- Seguridad perimetral: exposicion de servicios, TLS/certificados, cabeceras basicas, puertos abiertos y configuracion DNS.
- Gestion de datos: exportaciones CSV, adjuntos, repositorios compartidos, retencion, cifrado y trazabilidad.
- Pagos y facturacion: cambios de IBAN/datos fiscales, conciliacion, aprobaciones y evidencias.
- Continuidad: copias de seguridad, restauracion probada, alertas, dependencia de proveedores y plan de incidentes.
- Revision contractual: confidencialidad, tratamiento de datos, SLA, auditoria, notificacion de incidentes y subencargados.
- Informe final: matriz de riesgos, evidencias, severidad, esfuerzo estimado, responsables y plan de 30/60/90 dias.

## Estimacion de coste

No hay importes de auditoria en los archivos locales, asi que esta es una estimacion orientativa para presupuestar conversacion:

- Auditoria express: 3.000-5.000 EUR. Duracion aproximada: 1 semana. Cubre exposicion externa, accesos criticos, certificados y hallazgos principales.
- Auditoria estandar: 6.000-12.000 EUR. Duracion aproximada: 2-3 semanas. Cubre alcance recomendado completo con entrevistas, muestreo documental y plan de remediacion.
- Auditoria ampliada: 15.000-25.000 EUR. Duracion aproximada: 4-6 semanas. Incluye pruebas tecnicas mas profundas, revision de proveedores, procesos financieros y validacion de remediaciones.

Opcion recomendada para Sergio: auditoria estandar, con una primera entrega ejecutiva al final de la semana 1 para priorizar riesgos urgentes.

## Preguntas para Sergio Campos

- Que sistemas de Innotek son criticos para clientes y cuales tienen datos de pago, facturacion o datos personales?
- Hay inventario actualizado de certificados, dominios y responsables de renovacion?
- Se usan datos reales en demos o entornos de prueba?
- Como se autorizan cambios de datos fiscales, IBAN, licencias y accesos de proveedores?
- Que proveedores tienen acceso tecnico o administrativo a sistemas de Innotek?
- Existen evidencias recientes de restauracion de backup?
- Hay un procedimiento documentado de respuesta a incidentes?

## Propuesta de agenda de reunion

1. Confirmar alcance y activos criticos de Innotek.
2. Revisar riesgos inmediatos: certificados, accesos, exportaciones CSV, pagos y proveedores.
3. Elegir modalidad de auditoria: express, estandar o ampliada.
4. Acordar evidencias necesarias: contratos, inventario, accesos, politicas, backups y flujos de datos.
5. Definir calendario, responsables y primera entrega ejecutiva.

## Mensaje breve sugerido

Sergio, he preparado un enfoque de auditoria centrado en riesgos practicos: certificados, accesos, datos exportados, pagos/facturacion y proveedores. Mi recomendacion es empezar con una auditoria estandar de 2-3 semanas, dejando una primera entrega ejecutiva en la semana 1 para priorizar cualquier riesgo urgente. El rango orientativo seria 6.000-12.000 EUR, ajustable tras confirmar alcance y numero de sistemas.
