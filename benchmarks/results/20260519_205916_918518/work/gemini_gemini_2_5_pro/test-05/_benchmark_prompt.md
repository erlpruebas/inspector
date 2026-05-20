# Detectar gasto discrepante de febrero

Audita `benchmarks/assets/assistant_synthetic/gastos_2026_02.csv` e identifica la discrepancia de importe. Devuelve concepto, importe declarado, importe esperado y recomendacion.

Archivos locales preparados en el directorio de trabajo:
- `assistant_synthetic/gastos_2026_02.csv`

Usa esas rutas relativas cuando necesites leer datos locales.

Archivo de salida esperado: resultado.md.
Devuelve el contenido final o crea ese archivo en el directorio de trabajo.

Archivos disponibles en el directorio de trabajo:

### assistant_synthetic\gastos_2026_02.csv
```text
fecha,concepto,categoria,importe_declarado,importe_esperado,estado
PHONE_0091,Cena cliente,comidas,96.2,96.2,ok
PHONE_0090,PERSON_0075,viajes,62.0,62.0,ok
PHONE_0089,Licencia PDF,software,19.9,29.9,importe_discrepante

```