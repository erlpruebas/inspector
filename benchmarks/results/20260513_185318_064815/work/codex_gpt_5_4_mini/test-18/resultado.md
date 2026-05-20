Voy a revisar el CSV y la estructura disponible para segmentar los prospectos con criterios consistentes. Después prepararé una salida útil con empresa, ciudad, responsable sugerido y el motivo de prioridad.

Estoy confirmando el flujo de trabajo para CSVs antes de tocar nada. Luego voy a inspeccionar las columnas para definir una segmentación que no dependa de supuestos débiles.

Ya tengo la guía del trabajo: el CSV se puede importar directamente y luego segmentaré con un criterio de campaña, priorizando una salida clara y reutilizable. Primero voy a revisar las columnas reales y el contenido para definir la lógica de asignación.

Ya confirmé que hay 6 prospectos dentro de 50 contactos. Ahora estoy leyendo sus atributos completos para segmentarlos con una regla explícita y no con una asignación arbitraria.

Voy a materializar la segmentación en un entregable reutilizable. Haré un archivo `.xlsx` con los prospectos priorizados y una clasificación simple por campaña/responsable, además de validar que sólo entren los contactos tipo `prospecto`.

He terminado la lectura del CSV y ya tengo la lista de prospectos. Ahora voy a montar un pequeño generador para dejar el resultado en un `.xlsx` limpio y verificable, no sólo en texto suelto.

La librería de artefactos no está resolviendo desde este directorio todavía. Voy a localizar la dependencia compartida una sola vez y después enlazarla para poder construir el archivo sin improvisar rutas.

Estoy buscando la dependencia exacta del generador de hojas para evitar montar una solución casera. Si no aparece en el directorio compartido, pivotaré a una salida CSV/Markdown, pero primero agoto la vía correcta de artefacto.

Asumo que `responsable sugerido` significa el perfil interno que debería gestionar cada prospecto, no una persona ya asignada.

Segmentación de los `prospecto` detectados en `assistant_synthetic/contactos_50.csv`:

| Nombre | Empresa | Ciudad | Responsable sugerido | Motivo de prioridad |
|---|---|---:|---|---|
| Raquel Cano | Noda Labs | Madrid | Ejecutivo/a de cuentas senior / SDR especializado en data | Único prospecto con prioridad `alta`; además su rol es `Data`, lo que sugiere interés técnico y posible necesidad clara. |
| Paula Ferrer | BravoSoft | Malaga | Ejecutivo/a comercial | Rol `Ventas` y prioridad `media`; encaja bien en un abordaje comercial directo. |
| Fabiola Mendez | OptiRed | Murcia | Ejecutivo/a comercial | Rol `Ventas` y prioridad `media`; buena candidata para secuencia comercial estándar. |
| Helena Suarez | PuraVida | Alicante | Responsable de alianzas / desarrollo de negocio | Rol `Expansion`; prioridad `media`, orientada a crecimiento y posibles partnerships. |
| Miguel Santos | Argentalia | Madrid | Director/a comercial / cuentas estratégicas | Rol `Inversiones`; requiere enfoque más consultivo y de mayor valor por cuenta. |
| Valeria Navas | RedNova | Madrid | Responsable de marketing / demand gen | Rol `Marketing` y prioridad `media`; ideal para propuesta alineada con generación de demanda. |

Criterio usado:
- `alta` = contacto a tratar primero.
- `Ventas` = responsable comercial.
- `Data` = responsable consultivo/técnico.
- `Expansion` = desarrollo de negocio.
- `Marketing` = marketing/demand gen.
- `Inversiones` = cuentas estratégicas o dirección comercial.

Si quieres, puedo devolvértelo también en formato CSV o en una tabla lista para pegar en Excel.
