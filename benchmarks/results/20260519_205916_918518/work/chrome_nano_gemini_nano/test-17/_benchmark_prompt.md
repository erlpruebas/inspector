# Resumen financiero de gastos enero-mayo

Agrega los gastos de enero a mayo. Calcula total por mes, categorias principales y lista de anomalias.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/gastos_2026_01.csv`
- `assistant_synthetic/gastos_2026_02.csv`
- `assistant_synthetic/gastos_2026_03.csv`
- `assistant_synthetic/gastos_2026_04.csv`
- `assistant_synthetic/gastos_2026_05.csv`

Usa esas rutas relativas cuando necesites leer datos locales.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\gastos_2026_01.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0096,PERSON_0077,viajes,180.0,180.0,ok
PHONE_0095,Taxi aeropuerto,viajes,38.5,38.5,ok
PHONE_0094,Software encuestas,software,49.0,49.0,ok

```

### assistant_synthetic\gastos_2026_02.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0091,Cena cliente,comidas,96.2,96.2,ok
PHONE_0090,PERSON_0075,viajes,62.0,62.0,ok
PHONE_0089,Licencia PDF,software,19.9,29.9,importe_discrepante

```

### assistant_synthetic\gastos_2026_03.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0093,PERSON_0076,viajes,210.0,210.0,posible_duplicado
PHONE_0093,PERSON_0076,viajes,210.0,210.0,posible_duplicado
PHONE_0092,Comida equipo,comidas,134.7,134.7,ok

```

### assistant_synthetic\gastos_2026_04.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0008,Dominio anual,software,14.99,14.99,ok
PHONE_0098,Taxi cliente,viajes,28.3,28.3,sin_recibo
PHONE_0097,Material oficina,oficina,73.4,73.4,ok

```

### assistant_synthetic\gastos_2026_05.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0101,PERSON_0078,viajes,155.0,155.0,ok
PHONE_0100,Suscripcion IA,software,120.0,120.0,revisar_proveedor
PHONE_0099,Cafe reunion,comidas,18.4,18.4,ok

```