Voy a revisar el CSV para entender las columnas disponibles y luego armar una segmentación accionable con prioridad y responsable sugerido.

El archivo tiene las columnas necesarias (`empresa`, `ciudad`, `rol`, `tipo`, `prioridad`). Ahora filtro solo `tipo=prospecto` y revisaré la distribución por ciudad, prioridad y rol para proponer segmentos.

Encontré 6 contactos tipo `prospecto` en `assistant_synthetic/contactos_50.csv`.

| Segmento | Empresa | Ciudad | Responsable sugerido | Motivo de prioridad |
|---|---:|---|---|---|
| Prioridad alta | Noda Labs | Madrid | Especialista técnico / Data | Único prospecto con prioridad `alta`; perfil `Data`, buena entrada para propuesta técnica o demo avanzada. |
| Madrid - desarrollo comercial | Argentalia | Madrid | Ejecutivo comercial senior | Prospecto en Madrid con rol `Inversiones`; posible oportunidad estratégica o de ticket alto. |
| Madrid - marketing | RedNova | Madrid | Responsable de marketing / growth | Rol `Marketing`; adecuado para campaña orientada a captación, posicionamiento o automatización comercial. |
| Expansión regional | PuraVida | Alicante | Business development | Rol `Expansion`; buen encaje para propuesta de crecimiento o apertura de mercado. |
| Ventas regionales | BravoSoft | Malaga | Ejecutivo comercial | Rol `Ventas`; prioridad media, recomendable contacto directo con mensaje de mejora comercial. |
| Ventas regionales | OptiRed | Murcia | Ejecutivo comercial | Rol `Ventas`; prioridad media, agrupar con BravoSoft para campaña comercial regional. |

Recomendación de orden de campaña:

1. `Noda Labs` primero, por prioridad alta.
2. Los 3 prospectos de `Madrid`, porque concentran la mitad del pipeline prospecto.
3. `PuraVida`, por rol de expansión.
4. `BravoSoft` y `OptiRed` juntos en una secuencia comercial de prioridad media.
