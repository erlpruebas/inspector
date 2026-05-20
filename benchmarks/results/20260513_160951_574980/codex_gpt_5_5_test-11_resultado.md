Voy a leer el CSV local y revisar sus columnas para agrupar correctamente los clientes marcados como prioridad alta.

El archivo tiene columnas claras (`nombre`, `ciudad`, `empresa`, `tipo`, `prioridad`, etc.). Ahora filtro solo `tipo=cliente` y `prioridad=alta`, y preparo el resumen por ciudad.

Clientes con `tipo=cliente` y `prioridad=alta` en `assistant_synthetic/contactos_50.csv`:

| Ciudad | Clientes |
|---|---|
| A Coruna | Elena Vidal, Atlantic Data |
| Barcelona | Beatriz Costa, Orion Retail; Lorena Vidal, Civitas; Tomas Vega, Zenit Food; Xavier Puig, Barna Health |
| Bilbao | Laura Marin, Northwind ES |
| Cadiz | Lucia Torres, Soluciones Mar |
| Granada | Irene Sanz, BioCentro |
| Madrid | Alberto Saez, OmniPlus; Ana Lopez, Nova Iberia; Noelia Castro, Clinica Centro |
| Murcia | Ruben Ortega, MetalSur |
| Sevilla | Carlos Benitez, SolarDesk; Julia Iglesias, Tres Naves; Marta Ruiz, Clinica Sol |
| Valladolid | Guillermo Casas, NeoTaller |
| Zaragoza | Sergio Campos, Innotek |

Total: 17 clientes de alta prioridad.

Tres acciones comerciales recomendadas:

1. Priorizar campañas locales en Barcelona, Madrid y Sevilla, que concentran 10 de los 17 clientes.
2. Contactar primero a perfiles decisores: Direccion, Gerencia, CTO y Directora Operaciones.
3. Preparar propuestas segmentadas por sector/rol: operaciones, compras, administracion, IT/CTO y finanzas.
