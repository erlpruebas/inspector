Voy a revisar el CSV para entender las columnas disponibles y luego agruparé los prospectos con criterios explícitos de prioridad para la campaña.

El archivo trae una columna `tipo` y otra `prioridad`, así que filtraré por `tipo=prospecto` y usaré la prioridad existente combinada con rol/ciudad para sugerir responsable y motivo.

Encontré 6 contactos tipo `prospecto` en `assistant_synthetic/contactos_50.csv`.

| Segmento | Empresa | Ciudad | Contacto | Responsable sugerido | Motivo de prioridad |
|---|---|---:|---|---|---|
| Prioridad alta | Noda Labs | Madrid | Raquel Cano | Responsable de cuentas estratégicas / Data | Único prospecto con prioridad `alta`; rol de Data sugiere posible necesidad técnica o analítica. |
| Madrid - inversión | Argentalia | Madrid | Miguel Santos | Responsable comercial Madrid / Finanzas | Prospecto en Madrid con rol de Inversiones; buen encaje para propuesta de valor financiera o estratégica. |
| Madrid - marketing | RedNova | Madrid | Valeria Navas | Responsable comercial Madrid / Marketing | Prospecto en Madrid con rol de Marketing; puede priorizarse para campaña de generación de demanda. |
| Ventas - sur | BravoSoft | Málaga | Paula Ferrer | Responsable comercial zona sur | Rol de Ventas; contacto probablemente cercano a necesidades comerciales o crecimiento. |
| Expansión - levante | PuraVida | Alicante | Helena Suarez | Responsable expansión / zona levante | Rol de Expansión; posible interés en soluciones que escalen operaciones o apertura de mercado. |
| Ventas - levante | OptiRed | Murcia | Fabiola Mendez | Responsable comercial zona levante | Rol de Ventas; oportunidad comercial directa, aunque con prioridad `media`. |

Recomendación de orden para la campaña:

1. `Noda Labs` por prioridad alta.
2. `Argentalia` y `RedNova` por concentración en Madrid y roles estratégicos.
3. `BravoSoft`, `PuraVida` y `OptiRed` por encaje funcional con ventas/expansión en zonas sur y levante.
