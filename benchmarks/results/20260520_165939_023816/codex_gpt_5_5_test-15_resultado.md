Voy a leer las notas y el CSV de contactos para ver el formato exacto y cruzar menciones con nombres/empresas/emails de forma determinista.

Ya veo que las notas son transcripciones JSONL y los contactos tienen nombre, empresa y email. Ahora leeré todos los registros y haré el cruce por nombre completo, nombre de pila y empresa mencionada.

El cruce principal está claro: algunas notas mencionan nombre completo, otras solo nombre de pila junto a empresa, y unas pocas solo empresa. Incluiré los emparejamientos que tienen contacto único en el CSV; dejaré fuera notas sin contacto identificable.

Estos son los cruces encontrados. En `VN-009`, `VN-013` y `VN-019` la nota menciona solo la empresa; la persona se infiere por contacto único en el CSV.

| Tarea | Persona | Empresa | Email |
|---|---|---|---|
| Llamar para confirmar demo del módulo de pagos | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |
| Enviar CSV actualizado de monitores con descuento del 4% | Luis Martin | Delta Equipos | luis.martin@deltaequipos.es |
| Comprar billete si confirma reunión | Xavier Puig | Barna Health | xavier.puig@barnahealth.es |
| Preparar minuta con riesgos de seguridad y coste de auditoría | Sergio Campos | Innotek | sergio.campos@innotek.es |
| Pedir facturas de abril que no aparecen en el banco | Elena Vidal | Atlantic Data | elena.vidal@atlanticdata.es |
| Revisar contrato y responder antes del día 12 | David Navarro | IberLegal | david.navarro@iberlegal.es |
| Agendar seguimiento por administración | Marta Ruiz | Clinica Sol | marta.ruiz@clinicasol.es |
| Enviar informes en PDF con resumen ejecutivo corto | Ana Lopez | Nova Iberia | ana.lopez@novaiberia.es |
| Buscar alternativa barata a herramienta de encuestas | Clara Molina | GreenBox | clara.molina@greenbox.es |
| Llamar por pedido de licencias y confirmar dirección fiscal | Tomas Vega | Zenit Food | tomas.vega@zenitfood.es |
| Enviar agenda de implantación con hito de formación | Laura Marin | Northwind ES | laura.marin@northwind.es |
| Renovar certificado SSL antes del día 28 | Ivan Duran | Cobalto | ivan.duran@cobalto.es |
| Enviar email amable por propuesta sin respuesta | Paula Ferrer | BravoSoft | paula.ferrer@bravosoft.es |
| Incluir incidencias de facturación en informe mensual | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |
