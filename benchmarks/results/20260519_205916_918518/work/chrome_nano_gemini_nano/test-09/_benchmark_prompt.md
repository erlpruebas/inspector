# Auditar duplicados de marzo

Analiza `gastos_2026_03.csv` y detecta cargos duplicados. Calcula el impacto economico y la accion recomendada.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/gastos_2026_03.csv`

Usa esas rutas relativas cuando necesites leer datos locales.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\gastos_2026_03.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0093,PERSON_0076,viajes,210.0,210.0,posible_duplicado
PHONE_0093,PERSON_0076,viajes,210.0,210.0,posible_duplicado
PHONE_0092,Comida equipo,comidas,134.7,134.7,ok

```