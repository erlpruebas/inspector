# Tablero de acciones por responsable

Fuentes combinadas:
- `assistant_synthetic/notas_voz.jsonl`
- `assistant_synthetic/contactos_50.csv`
- `assistant_synthetic/emails_hilos.md`

Criterio usado:
- `Prioridad` = prioridad del contacto cuando existe; en acciones internas se infiere por urgencia.
- `Fecha limite` = fecha absoluta cuando el texto lo permite. Las referencias relativas o condicionales se marcan como `aprox.`.

## Resumen por responsable
| Responsable | Empresa / area | Tipo | Prioridad | Acciones | Proxima fecha limite |
| --- | --- | --- | --- | ---: | --- |
| Ana Lopez | Nova Iberia / Directora Operaciones | cliente | alta | 2 | - |
| David Navarro | IberLegal / Legal | proveedor | media | 2 | 2026-05-12 |
| Elena Vidal | Atlantic Data / Finanzas | cliente | alta | 1 | - |
| Equipo interno | Finanzas, IT, Operaciones, CRM, analisis y administracion | interno | mixta | 9 | 2026-05-15 09:30 |
| Laura Marin | Northwind ES / Ventas | cliente | alta | 1 | 2026-05-22 |
| Luis Martin | Delta Equipos / Compras | proveedor | media | 2 | 2026-05-13 |
| Marta Ruiz | Clinica Sol / Administracion | cliente | alta | 1 | 2026-05-05 16:00 |
| Noelia Castro | Clinica Centro / Administracion | cliente | alta | 2 | 2026-05-07 |
| Paula Ferrer | BravoSoft / Ventas | prospecto | media | 2 | 2026-05-09 aprox. |
| Sergio Campos | Innotek / CTO | cliente | alta | 1 | - |
| Tomas Vega | Zenit Food / Compras | cliente | alta | 1 | - |
| Xavier Puig | Barna Health / IT | cliente | alta | 2 | 2026-05-18 10:00 |

## Tablero detallado
| Responsable | Empresa / area | Tipo | Accion | Prioridad | Fecha limite | Fuente |
| --- | --- | --- | --- | --- | --- | --- |
| Marta Ruiz | Clinica Sol / Administracion | cliente | Agendar seguimiento con Marta Ruiz por administracion. | alta | 2026-05-05 16:00 | VN-007 |
| Noelia Castro | Clinica Centro / Administracion | cliente | Llamar a Noelia para confirmar la demo del modulo de pagos. | alta | 2026-05-07 | VN-001 |
| Paula Ferrer | BravoSoft / Ventas | prospecto | Enviar un correo amable a Paula Ferrer sobre la propuesta de BravoSoft. | media | 2026-05-09 aprox. | VN-015 |
| Paula Ferrer | BravoSoft / Ventas | prospecto | Revisar la propuesta con direccion y responder la semana que viene; si no hay respuesta, insistir con un correo corto. | media | 2026-05-09 aprox. | E-006 |
| David Navarro | IberLegal / Legal | proveedor | Revisar contrato de IberLegal y responder a David antes del 12. | media | 2026-05-12 | VN-006 |
| David Navarro | IberLegal / Legal | proveedor | Enviar comentarios sobre la clausula 8 y la renovacion automatica antes del 12 de mayo. | media | 2026-05-12 | E-003 |
| Luis Martin | Delta Equipos / Compras | proveedor | Cerrar antes del dia 13 para aplicar el 4% de descuento en monitores 27. | media | 2026-05-13 | E-002 |
| Noelia Castro | Clinica Centro / Administracion | cliente | Preparar la demo de pagos centrada en conciliacion y estado de pagos. | alta | 2026-05-14 11:30 | E-001 |
| Equipo interno | Administracion | interno | Reservar la sala para la reunion interna del viernes a las 9:30. | media | 2026-05-15 09:30 | VN-020 |
| Xavier Puig | Barna Health / IT | cliente | Comprar billete para Barcelona si Xavier confirma la reunion de Barna Health. | alta | 2026-05-18 | VN-003 |
| Xavier Puig | Barna Health / IT | cliente | Confirmar reunion presencial en Barcelona y revisar integracion con SSO. | alta | 2026-05-18 10:00 | E-004 |
| Laura Marin | Northwind ES / Ventas | cliente | Enviar agenda de implantacion a Laura e incluir el hito de formacion del dia 22. | alta | 2026-05-22 | VN-011 |
| Equipo interno | IT / Seguridad | interno | Renovar el certificado SSL de Cobalto antes del 28. | alta | 2026-05-28 | VN-013 |
| Ana Lopez | Nova Iberia / Directora Operaciones | cliente | Enviar informes a Ana Lopez en PDF con resumen ejecutivo corto. | alta | - | VN-008 |
| Ana Lopez | Nova Iberia / Directora Operaciones | cliente | Enviar siempre informes en PDF con una pagina de resumen ejecutivo y anexos separados. | alta | - | E-005 |
| Elena Vidal | Atlantic Data / Finanzas | cliente | Pedir a Elena Vidal las facturas de abril que faltan en el banco. | alta | - | VN-005 |
| Luis Martin | Delta Equipos / Compras | proveedor | Enviar a Luis el CSV actualizado de monitores con el 4% de descuento. | media | - | VN-002 |
| Sergio Campos | Innotek / CTO | cliente | Preparar minuta con riesgos de seguridad y coste de auditoria para Sergio Campos. | alta | - | VN-004 |
| Tomas Vega | Zenit Food / Compras | cliente | Llamar a Tomas de Zenit Food para licencias y confirmar direccion fiscal. | alta | - | VN-010 |
| Equipo interno | Finanzas | interno | Revisar gastos de marzo y los dos cargos duplicados de hotel. | alta | - | VN-012 |
| Equipo interno | Finanzas | interno | Cruzar pagos de Norte SA con facturas y localizar la de 847.50. | alta | - | VN-016 |
| Equipo interno | CRM / Ventas | interno | Crear una lista de contactos prioritarios de Madrid con nivel alta. | media | - | VN-017 |
| Equipo interno | Analisis | interno | Investigar si Apple ha subido mas que Microsoft en los ultimos seis meses. | baja | - | VN-018 |
| Equipo interno | Automatizacion | interno | Preparar comparativa OpenRouter vs Gemini para tareas de ofimatica. | media | - | VN-014 |
| Equipo interno | GreenBox / compras | interno | Buscar una alternativa barata a herramienta de encuestas para GreenBox. | media | - | VN-009 |
| Equipo interno | Operaciones / facturacion | interno | Preparar el informe mensual de incidencias incluyendo Clinica Centro y facturacion. | media | - | VN-019 |
