# Informe de discrepancias de gastos Q1

Audita los gastos de enero, febrero y marzo en los CSV correspondientes. Resume discrepancias, duplicados y partidas limpias.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/gastos_2026_01.csv`
- `assistant_synthetic/gastos_2026_02.csv`
- `assistant_synthetic/gastos_2026_03.csv`

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