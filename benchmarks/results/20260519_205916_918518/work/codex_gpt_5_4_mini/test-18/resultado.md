Voy a revisar el CSV y segmentar solo los contactos tipo `prospecto`, sacando empresa, ciudad, responsable sugerido y motivo de prioridad. Primero inspecciono la estructura del archivo para decidir el criterio de segmentación.

Ya tengo la guía de trabajo para CSVs. Ahora inspecciono columnas y unas muestras del archivo para segmentar con un criterio coherente y no asumir campos que no existan.

He identificado 6 contactos tipo `prospecto` en el archivo.

| Empresa | Ciudad | Responsable sugerido | Motivo de prioridad |
|---|---|---|---|
| Noda Labs | Madrid | KAM senior / preventa técnica | `prioridad = alta` y rol `Data`, lo que sugiere un caso de mayor valor y necesidad más técnica. |
| BravoSoft | Málaga | Ejecutivo comercial regional | `prioridad = media`; rol `Ventas`, encaje directo para seguimiento comercial. |
| PuraVida | Alicante | Responsable de alianzas / expansión | `prioridad = media`; rol `Expansion`, buena opción para desarrollo de negocio. |
| Argentalia | Madrid | Desarrollo de negocio / KAM | `prioridad = media`; rol `Inversiones`, perfil más estratégico que transaccional. |
| RedNova | Madrid | Ejecutivo comercial / marketing solutions | `prioridad = media`; rol `Marketing`, posible oportunidad de campaña o cross-sell. |
| OptiRed | Murcia | Ejecutivo comercial regional | `prioridad = media`; rol `Ventas`, seguimiento comercial estándar. |

Segmentación rápida:
- `Alta prioridad`: 1 prospecto
- `Media prioridad`: 5 prospectos

Si quieres, puedo devolvértelo también en formato CSV o agruparlo por responsable sugerido.
