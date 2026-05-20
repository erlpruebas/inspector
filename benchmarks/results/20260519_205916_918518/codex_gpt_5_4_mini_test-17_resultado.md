Voy a leer los cinco CSV locales, consolidar el gasto de enero a mayo y sacar tres bloques: total por mes, categorías principales y anomalías detectables.

Ya vi que los CSV tienen una estructura algo rara: la primera columna se llama `fecha`, pero los valores parecen identificadores tipo `PHONE_0096`. Voy a leer el contenido completo para no asumir mal el mapeo y calcular el resumen sobre los importes reales.

Voy a consolidar los importes por archivo-mes y por categoría, y además revisar estados anómalos, discrepancias entre `importe_declarado` y `importe_esperado`, y filas duplicadas exactas.

Ya tengo el consolidado. Me falta solo una pasada para sacar porcentajes por categoría y, si aporta valor, el total depurado opcional para distinguir gasto bruto vs. gasto sin duplicados.

**Resumen enero-mayo 2026**

Tomé los 5 CSV locales y calculé el gasto usando `importe_declarado`. Ojo: la columna `fecha` no trae una fecha real, sino IDs tipo `PHONE_0096`, así que el mes se infiere del nombre del archivo.

- Total bruto enero-mayo: `1,410.39`

**Total por mes**
- Enero: `267.50`
- Febrero: `178.10`
- Marzo: `554.70`
- Abril: `116.69`
- Mayo: `293.40`

**Categorías principales**
- `viajes`: `883.80`  `62.7%`
- `comidas`: `249.30`  `17.7%`
- `software`: `203.89`  `14.5%`
- `oficina`: `73.40`  `5.2%`

**Anomalías detectadas**
- Febrero, `Licencia PDF`: `importe_declarado=19.90` vs `importe_esperado=29.90`, estado `importe_discrepante`  
- Marzo, `PERSON_0076` / `viajes`: fila duplicada exacta, estado `posible_duplicado`  
- Abril, `Taxi cliente`: estado `sin_recibo`  
- Mayo, `Suscripcion IA`: estado `revisar_proveedor`  

**Nota**
- Si elimino el duplicado exacto de marzo, el total baja a `1,200.39`.
- Si además corrijo la discrepancia de febrero al importe esperado, quedaría en `1,210.39`.

Si quieres, también puedo devolverte esto en una tabla CSV o en formato listo para pegar en Excel.
