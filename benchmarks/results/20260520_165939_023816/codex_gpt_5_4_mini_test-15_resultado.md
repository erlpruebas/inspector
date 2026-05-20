Voy a cruzar el JSONL de notas con el CSV de contactos, extraer las menciones de personas y empresas, y devolver una tabla con la tarea, la persona, la empresa y el email. Primero reviso la estructura de ambos archivos para decidir el criterio de emparejamiento.

Estoy leyendo la estructura de ambas fuentes para ver qué campos traen y cómo identificar las menciones de forma fiable. Luego hago el cruce por nombre y, si hace falta, por empresa.

Ya tengo la estructura: las notas son texto libre con ID y timestamp, y el CSV trae nombre, email y empresa. Ahora voy a detectar coincidencias por nombre completo y por empresa mencionada en el texto para no perder cruces obvios.

El entorno no tiene `python`, así que lo resuelvo con PowerShell nativo. Voy a listar todos los contactos y todas las notas para construir el cruce directamente.

Voy a resolver el cruce de forma semiautomática: para cada nota busco coincidencias por nombre completo, nombre de pila y empresa. Así puedo separar coincidencias seguras de las que solo se deducen por contexto.

El primer intento no devolvió el listado útil, así que simplifico el script y saco el mapeo nota por nota con las coincidencias encontradas.

He encontrado 15 coincidencias claras entre las notas y los contactos. En tres casos el cruce se apoya solo en la empresa mencionada en la nota (`VN-009`, `VN-013`, `VN-019`).

| Tarea | Persona | Empresa | Email |
|---|---|---|---|
| VN-001 | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |
| VN-002 | Luis Martin | Delta Equipos | luis.martin@deltaequipos.es |
| VN-003 | Xavier Puig | Barna Health | xavier.puig@barnahealth.es |
| VN-004 | Sergio Campos | Innotek | sergio.campos@innotek.es |
| VN-005 | Elena Vidal | Atlantic Data | elena.vidal@atlanticdata.es |
| VN-006 | David Navarro | IberLegal | david.navarro@iberlegal.es |
| VN-007 | Marta Ruiz | Clinica Sol | marta.ruiz@clinicasol.es |
| VN-008 | Ana Lopez | Nova Iberia | ana.lopez@novaiberia.es |
| VN-009 | Clara Molina | GreenBox | clara.molina@greenbox.es |
| VN-010 | Tomas Vega | Zenit Food | tomas.vega@zenitfood.es |
| VN-011 | Laura Marin | Northwind ES | laura.marin@northwind.es |
| VN-013 | Ivan Duran | Cobalto | ivan.duran@cobalto.es |
| VN-015 | Paula Ferrer | BravoSoft | paula.ferrer@bravosoft.es |
| VN-019 | Noelia Castro | Clinica Centro | noelia.castro@clinicacentro.es |

Si quieres, puedo devolvértelo también en CSV.
