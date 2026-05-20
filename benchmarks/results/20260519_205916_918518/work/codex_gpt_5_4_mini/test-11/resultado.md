Voy a leer el CSV, identificar los clientes con prioridad alta y resumirlos por ciudad antes de proponer tres acciones comerciales.

Ya tengo la guía del CSV. Ahora voy a identificar la estructura de columnas y extraer solo los registros con prioridad alta para agruparlos por ciudad.

Estoy comprobando si “cliente” en la columna `tipo` cambia el conjunto, porque el archivo también contiene `proveedor` y `partner`. Voy a filtrar por `tipo=cliente` y `prioridad=alta` para evitar mezclar contactos que no son clientes.

He tomado `cliente` como `tipo=cliente` y `prioridad=alta`. Bajo ese criterio hay **17 clientes de alta prioridad** en `contactos_50.csv`.

**Agrupados por ciudad**

- **Barcelona (4)**
  - `PERSON_0043` | `PERSON_0042` | `Retail` | `EMAIL_0035` | `PHONE_0042`
  - `PERSON_0027` | `PERSON_0026` | `Compras` | `EMAIL_0020` | `PHONE_0027`
  - `PERSON_0024` | `Barna Health` | `IT` | `EMAIL_0018` | `PHONE_0025`
  - `PERSON_0013` | `Civitas` | `Producto` | `EMAIL_0007` | `PHONE_0014`

- **Madrid (3)**
  - `PERSON_0069` | `PERSON_0068` | `PERSON_0067` | `EMAIL_0055` | `PHONE_0062`
  - `PERSON_0001` | `ORG_0005` | `Administracion` | `EMAIL_0025` | `PHONE_0032`
  - `PERSON_0022` | `OmniPlus` | `Direccion` | `EMAIL_0016` | `PHONE_0023`

- **Sevilla (3)**
  - `PERSON_0064` | `Clinica Sol` | `Administracion` | `EMAIL_0053` | `PHONE_0060`
  - `PERSON_0036` | `PERSON_0035` | `Direccion` | `EMAIL_0029` | `PHONE_0036`
  - `PERSON_0020` | `SolarDesk` | `Operaciones` | `EMAIL_0014` | `PHONE_0021`

- **A Coruna (1)**
  - `PERSON_0062` | `PERSON_0061` | `Finanzas` | `EMAIL_0051` | `PHONE_0058`

- **Bilbao (1)**
  - `PERSON_0033` | `Northwind ES` | `Ventas` | `EMAIL_0027` | `PHONE_0034`

- **Cadiz (1)**
  - `PERSON_0053` | `PERSON_0052` | `Direccion` | `EMAIL_0043` | `PHONE_0050`

- **Granada (1)**
  - `PERSON_0047` | `BioCentro` | `Calidad` | `EMAIL_0039` | `PHONE_0046`

- **Murcia (1)**
  - `PERSON_0056` | `MetalSur` | `Gerencia` | `EMAIL_0046` | `PHONE_0053`

- **Valladolid (1)**
  - `PERSON_0016` | `NeoTaller` | `Gerencia` | `EMAIL_0010` | `PHONE_0017`

- **Zaragoza (1)**
  - `PERSON_0060` | `Innotek` | `CTO` | `EMAIL_0050` | `PHONE_0057`

**Tres acciones comerciales recomendadas**

1. **Priorizar cobertura por densidad geográfica**
   - Atacar primero **Barcelona, Madrid y Sevilla**, porque concentran 10 de los 17 clientes de alta prioridad.
   - Organiza cadencias y visitas por ciudad para reducir coste comercial y acelerar cierres.

2. **Personalizar el mensaje por rol**
   - Hay perfiles de **Dirección, Gerencia, CTO, Finanzas, Compras y Operaciones**.
   - Prepara propuestas distintas: valor económico para Finanzas/Compras, eficiencia operativa para Operaciones, y impacto estratégico para Dirección/CTO/Gerencia.

3. **Activar un plan de seguimiento en 48-72 horas**
   - Llama primero a los contactos con cargo más decisor: **Dirección, Gerencia y CTO**.
   - Después, envía una propuesta breve con siguiente paso claro: demo, diagnóstico o reunión de 20 minutos.

Si quieres, puedo también sacar la **lista completa de prioridad alta sin filtrar por tipo**, por si quieres incluir proveedores y partners en el plan comercial.
