Voy a leer las notas y el CSV de contactos, cruzar menciones de personas y empresas, y luego devolver una tabla con `tarea`, `persona`, `empresa` y `email`. Primero reviso la estructura de los archivos para extraer los campos correctos.

Ya tengo la guía para tratar CSV/JSONL. Ahora voy a inspeccionar los archivos de entrada para ver qué campos traen y cómo identificar las menciones de personas y empresas en las notas de voz.

La estructura es simple: JSONL con `id`, `timestamp` y `transcript`, y un CSV de contactos con `nombre`, `email` y `empresa`. Voy a recorrer todos los registros para localizar las menciones exactas y emparejarlas con el contacto correcto.

Ya tengo los cruces claros: varias notas nombran personas exactas del CSV y otras solo mencionan empresas o no tienen un contacto identificable. Voy a normalizar los nombres y sacar solo las coincidencias respaldadas por ambos archivos.

La coincidencia quedó resuelta: 11 notas apuntan a contactos del CSV con nombre suficiente para emparejar. Las demás notas no traen una persona identificable de forma segura, así que las excluyo para no inventar cruces.

He cruzado las notas con el CSV de contactos. Estas son las coincidencias seguras:

| tarea | persona | empresa | email |
|---|---|---|---|
| Llamar para confirmar la demo del módulo de pagos | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |
| Enviar el CSV actualizado de monitores | Luis Martin | Delta Equipos | luis.martin@deltaequipos.es |
| Confirmar la reunión antes de comprar el billete | Xavier Puig | Barna Health | xavier.puig@barnahealth.es |
| Preparar minuta con riesgos de seguridad y coste de auditoría | Sergio Campos | Innotek | sergio.campos@innotek.es |
| Pedir las facturas de abril | Elena Vidal | Atlantic Data | elena.vidal@atlanticdata.es |
| Revisar contrato y pedir respuesta antes del 12 | David Navarro | IberLegal | david.navarro@iberlegal.es |
| Agendar seguimiento por el tema de administración | Marta Ruiz | Clinica Sol | marta.ruiz@clinicasol.es |
| Enviar informes en PDF y resumen ejecutivo corto | Ana Lopez | Nova Iberia | ana.lopez@novaiberia.es |
| Llamar por pedido de licencias y confirmar dirección fiscal | Tomas Vega | Zenit Food | tomas.vega@zenitfood.es |
| Enviar agenda de implantación | Laura Marin | Northwind ES | laura.marin@northwind.es |
| Enviar email sobre la propuesta pendiente | Paula Ferrer | BravoSoft | paula.ferrer@bravosoft.es |

Si quieres, también te puedo devolver la misma tabla en formato CSV.
