Voy a revisar el CSV para entender sus columnas y criterios disponibles, y luego preparo una segmentación accionable para campaña con empresa, ciudad, responsable sugerido y motivo de prioridad.

El archivo tiene campos suficientes para priorizar directamente (`tipo`, `prioridad`, `ciudad`, `rol`, `empresa`). Ahora filtro solo `prospecto` y revisaré distribución por prioridad/ciudad para asignar responsables de forma consistente.

Segmenté 6 contactos tipo `prospecto` del archivo `assistant_synthetic/contactos_50.csv`.

| Segmento | Empresa | Ciudad | Responsable sugerido | Motivo de prioridad |
|---|---|---:|---|---|
| Prioridad alta | Noda Labs | Madrid | Responsable Key Accounts / Enterprise | Único prospecto con prioridad `alta`; perfil `Data`, buen encaje para propuesta consultiva o técnica. |
| Madrid - nurturing comercial | Argentalia | Madrid | Responsable Comercial Madrid | Prospecto de prioridad `media`; rol `Inversiones`, requiere mensaje orientado a ROI y crecimiento. |
| Madrid - marketing | RedNova | Madrid | Responsable Growth / Marketing | Prospecto de prioridad `media`; rol `Marketing`, adecuado para campaña de captación con casos de uso y métricas. |
| Sur - ventas | BravoSoft | Málaga | Responsable Comercial Sur | Prospecto de prioridad `media`; rol `Ventas`, buen candidato para campaña enfocada en eficiencia comercial. |
| Levante - expansión | PuraVida | Alicante | Responsable Comercial Levante | Prospecto de prioridad `media`; rol `Expansion`, conviene priorizar propuesta ligada a apertura de mercado. |
| Levante - ventas | OptiRed | Murcia | Responsable Comercial Levante | Prospecto de prioridad `media`; rol `Ventas`, puede agruparse con Alicante para una cadencia regional. |

Recomendación de orden de contacto: empezar por `Noda Labs`, seguir con los 3 prospectos de Madrid por concentración geográfica, y después ejecutar una secuencia regional para Levante/Sur.
