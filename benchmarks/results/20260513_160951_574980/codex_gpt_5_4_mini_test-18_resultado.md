Voy a revisar el CSV y preparar una segmentación práctica con empresa, ciudad, responsable sugerido y motivo de prioridad. Primero confirmo la estructura del archivo para decidir el criterio de segmentación.

Ya vi la estructura: el archivo trae `nombre`, `ciudad`, `empresa`, `rol`, `tipo` y `prioridad`. Ahora voy a filtrar solo los contactos `tipo=prospecto` y armar la segmentación con un responsable sugerido según rol y prioridad.

Estoy extrayendo solo los prospectos para evitar mezclar clientes/proveedores/partners. Después asigno un responsable sugerido con reglas simples: ventas para decisores comerciales, operaciones para perfiles operativos y alianzas para socios potenciales.

He segmentado los `prospecto` del archivo en 6 contactos. Los ordené por prioridad y encaje de rol para sugerir un responsable interno.

| Empresa | Ciudad | Responsable sugerido | Motivo de prioridad |
|---|---|---|---|
| Noda Labs | Madrid | Account Executive senior | Único prospecto con prioridad alta; además el rol `Data` sugiere necesidad técnica y potencial valor estratégico. |
| BravoSoft | Malaga | SDR / Ventas | Rol `Ventas`, encaje directo con una gestión comercial rápida. |
| OptiRed | Murcia | SDR / Ventas | Rol `Ventas`, oportunidad comercial clara y de contacto inmediato. |
| RedNova | Madrid | Marketing / Growth | Rol `Marketing`, útil para una campaña de generación de demanda o automatización. |
| PuraVida | Alicante | Business Development / Alianzas | Rol `Expansion`, sugiere apertura a partnership o crecimiento de canales. |
| Argentalia | Madrid | KAM senior / Dirección comercial | Rol `Inversiones`, conviene abordarlo con un perfil senior y mensaje de alto impacto. |

Segmentación práctica:
- `Prioridad alta`: Noda Labs
- `Prioridad media comercial`: BravoSoft, OptiRed
- `Prioridad media estratégica`: RedNova, PuraVida, Argentalia

Si quieres, puedo convertir esto en una tabla CSV lista para pegar en CRM o en una segmentación más accionable por `tipo de campaña` y `guion de contacto`.
