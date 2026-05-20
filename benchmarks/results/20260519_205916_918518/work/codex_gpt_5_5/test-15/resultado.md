Voy a leer las notas y el CSV de contactos para ver el formato y luego cruzar menciones de personas con sus empresas y emails.

Ya veo que las notas mezclan nombres reales, identificadores `PERSON_…` y empresas. Ahora voy a parsear todos los registros y buscar coincidencias contra el fichero de contactos.

El cruce directo encuentra varias notas por `PERSON_…` y otras por empresa. También hay menciones sin contacto disponible en el CSV, como `PERSON_0074`, `PERSON_0073`, `PERSON_0072`, `ORG_0007` y `ORG_0008`; las separaré para no inventar emails.

He cruzado `notas_voz.jsonl` con `contactos_50.csv`. Resultado:

| Tarea | Persona | Empresa | Email |
|---|---:|---:|---:|
| VN-001: Llamar antes del jueves y confirmar módulo de pagos | Noelia / PERSON_0001 | ORG_0005 | EMAIL_0025 |
| VN-003: Comprar billete si confirma la reunión | Xavier / PERSON_0024 | Barna Health | EMAIL_0018 |
| VN-004: Preparar minuta de riesgos y auditoría | PERSON_0060 | Innotek | EMAIL_0050 |
| VN-006: Revisar contrato y responder antes del 12 | David / PERSON_0058 | IberLegal | EMAIL_0048 |
| VN-007: Agendar seguimiento martes a las cuatro | PERSON_0064 | Clinica Sol | EMAIL_0053 |
| VN-008: Enviar informes en PDF con resumen corto | PERSON_0069 | PERSON_0068 | EMAIL_0055 |
| VN-009: Buscar alternativa barata de encuestas | PERSON_0057 | GreenBox | EMAIL_0047 |
| VN-011: Enviar agenda de implantación con hito de formación | PERSON_0033 | Northwind ES | EMAIL_0027 |
| VN-013: Renovar certificado SSL antes del 28 | PERSON_0037 | Cobalto | EMAIL_0030 |
| VN-015: Enviar email amable sobre propuesta | PERSON_0059 | BravoSoft | EMAIL_0049 |

Sin cruce en contactos: `PERSON_0074`, `PERSON_0073`, `PERSON_0072`, `ORG_0007`, `ORG_0008`.
