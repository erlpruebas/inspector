Voy a leer el CSV y resumir los clientes de prioridad alta por ciudad, luego sacar tres acciones comerciales concretas basadas en la distribución.

Ya tengo el criterio de trabajo. Ahora voy a inspeccionar la estructura del CSV para identificar la columna de prioridad y agrupar los clientes de prioridad alta por ciudad.

Ya tengo la agrupación inicial. Voy a sacar el listado exacto de clientes de prioridad alta por ciudad para evitar truncamientos y darte una salida limpia.

He filtrado `prioridad = alta` en `assistant_synthetic/contactos_50.csv`.

Hay 23 clientes de prioridad alta repartidos en 11 ciudades.

**Agrupados por ciudad**
- A Coruna: Elena Vidal (Atlantic Data, Finanzas)
- Barcelona: Beatriz Costa (Orion Retail, Retail), Lorena Vidal (Civitas, Producto), Tomas Vega (Zenit Food, Compras), Xavier Puig (Barna Health, IT)
- Bilbao: Laura Marin (Northwind ES, Ventas)
- Cadiz: Lucia Torres (Soluciones Mar, Direccion)
- Granada: Irene Sanz (BioCentro, Calidad)
- Madrid: Alberto Saez (OmniPlus, Direccion), Ana Lopez (Nova Iberia, Directora Operaciones), Esteban Lozano (Helixia, CTO), Hector Mora (FinanSys, Producto), Ivan Duran (Cobalto, Seguridad), Noelia Castro (Clinica Centro, Administracion), Raquel Cano (Noda Labs, Data), Samuel Ibanez (Quantica, Analitica)
- Murcia: Ruben Ortega (MetalSur, Gerencia)
- Sevilla: Carlos Benitez (SolarDesk, Operaciones), Julia Iglesias (Tres Naves, Direccion), Marta Ruiz (Clinica Sol, Administracion)
- Valencia: Gonzalo Pardo (MintCloud, Cloud)
- Valladolid: Guillermo Casas (NeoTaller, Gerencia)
- Zaragoza: Sergio Campos (Innotek, CTO)

**Tres acciones comerciales recomendadas**
1. Priorizar Madrid y Barcelona: concentran 12 de los 23 clientes de alta prioridad, así que ahí está el mayor retorno inmediato.
2. Hacer acercamiento por rol: en Madrid hay decisores de dirección, operaciones, CTO, datos y seguridad; conviene preparar mensajes distintos por área funcional.
3. Lanzar un plan de seguimiento por ciudad con cadencia corta: llamada inicial, email de valor y reunión de diagnóstico para Sevilla, Barcelona y Madrid, y luego cubrir el resto de ciudades con enfoque más ligero.

Si quieres, también puedo convertir esto en una tabla con `ciudad`, `cliente`, `empresa` y `rol` para que la puedas pegar en Excel o CRM.
