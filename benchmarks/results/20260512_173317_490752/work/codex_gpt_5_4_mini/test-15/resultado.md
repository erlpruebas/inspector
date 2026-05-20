Voy a leer las dos fuentes locales, extraer las personas mencionadas en las notas de voz y cruzarlas con el CSV de contactos para armar la tabla final.

Ya tengo un primer muestreo: las notas de voz traen nombres explícitos y el CSV incluye nombre, email y empresa. Ahora voy a listar todas las notas y hacer el cruce completo sin asumir coincidencias parciales.

Estoy validando el cruce con reglas simples: nombre completo, nombre parcial y compañía. Así evito meter filas que solo sean contexto de la nota y no una persona identificable.

He cruzado las notas con los contactos. En `VN-009` y `VN-019` la nota menciona solo la empresa, así que he resuelto el contacto único asociado a esa empresa.

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
