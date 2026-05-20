Voy a leer las dos fuentes locales, identificar las menciones de personas en las notas de voz y cruzarlas con el CSV de contactos para sacar una tabla con tarea, persona, empresa y email. Primero revisaré el esquema y una muestra de ambos archivos para ver cómo está nombrada la información.

Ya vi el formato: las notas traen un `id` y un texto libre, y el CSV tiene `nombre`, `empresa` y `email`. Ahora voy a extraer todos los nombres del CSV y buscar coincidencias en cada transcripción para construir el cruce sin perder casos por tildes o variaciones de orden.

Estoy sacando las coincidencias de forma mecánica para evitar errores de lectura: primero busco el nombre completo del contacto en la nota, y cuando aparece solo el nombre de pila junto con la empresa, lo cruzo con el registro correcto del CSV. Luego reviso los casos ambiguos antes de cerrar la tabla.

Hay dos notas que solo mencionan empresa y no nombre propio. Voy a comprobar si la empresa aparece una sola vez en el CSV; si es así, las trataré como referencias a ese contacto porque no hay ambigüedad real.

He cruzado las notas con el CSV y saqué estas coincidencias. En `VN-009`, `VN-013` y `VN-019` la nota menciona solo la empresa, así que el contacto se infiere porque en el CSV esa empresa aparece una sola vez.

| Tarea | Persona | Empresa | Email |
|---|---|---|---|
| VN-001: llamar a Noelia antes del jueves para confirmar demo del módulo de pagos | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |
| VN-002: enviar a Luis el CSV actualizado de monitores | Luis Martin | Delta Equipos | luis.martin@deltaequipos.es |
| VN-003: comprar billete para Barcelona si Xavier confirma la reunión | Xavier Puig | Barna Health | xavier.puig@barnahealth.es |
| VN-004: preparar minuta con riesgos de seguridad y coste de auditoría | Sergio Campos | Innotek | sergio.campos@innotek.es |
| VN-005: pedir las facturas de abril | Elena Vidal | Atlantic Data | elena.vidal@atlanticdata.es |
| VN-006: revisar contrato de IberLegal y responder antes del 12 | David Navarro | IberLegal | david.navarro@iberlegal.es |
| VN-007: agendar seguimiento por el tema de administración | Marta Ruiz | Clinica Sol | marta.ruiz@clinicasol.es |
| VN-008: recordar que prefiere informes en PDF y resumen ejecutivo corto | Ana Lopez | Nova Iberia | ana.lopez@novaiberia.es |
| VN-009: buscar alternativa barata a herramienta de encuestas | Clara Molina | GreenBox | clara.molina@greenbox.es |
| VN-010: llamar por pedido de licencias y confirmar dirección fiscal | Tomas Vega | Zenit Food | tomas.vega@zenitfood.es |
| VN-011: enviar agenda de implantación e incluir hito de formación | Laura Marin | Northwind ES | laura.marin@northwind.es |
| VN-013: poner recordatorio para renovar certificado SSL | Ivan Duran | Cobalto | ivan.duran@cobalto.es |
| VN-015: enviar email amable por la propuesta no contestada | Paula Ferrer | BravoSoft | paula.ferrer@bravosoft.es |
| VN-019: preparar informe mensual de incidencias y facturación | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |

Si quieres, también puedo devolvértelo en CSV o añadir una columna con el `id` de la nota de voz.
