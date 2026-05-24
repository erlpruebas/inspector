# Informe de Auditoría de Gastos (Enero - Mayo 2026)

## Resumen Ejecutivo

Se realizó una auditoría de los gastos registrados desde enero hasta mayo de 2026. El objetivo fue identificar anomalías como gastos duplicados, falta de recibos y discrepancias en los importes, para luego proponer recomendaciones de control interno.

Se detectaron varias incidencias, incluyendo un gasto duplicado, una ausencia de recibo y una discrepancia de importe.

## Hallazgos de la Auditoría

### 1. Gastos Duplicados

*   **Detalle:** Se identificó una entrada de gasto idéntica registrada dos veces.
*   **Incidencia:**
    *   `2026-03-04, Hotel Barcelona, viajes, 210.0, 210.0, posible_duplicado`
    *   `2026-03-04, Hotel Barcelona, viajes, 210.0, 210.0, posible_duplicado`

### 2. Recibos Faltantes

*   **Detalle:** Se encontró un gasto sin el recibo correspondiente adjunto.
*   **Incidencia:**
    *   `2026-04-11, Taxi cliente, viajes, 28.3, 28.3, sin_recibo`

### 3. Discrepancias de Importe

*   **Detalle:** Se observó una diferencia entre el importe declarado y el importe esperado para un gasto específico.
*   **Incidencia:**
    *   `2026-02-22, Licencia PDF, software, 19.9, 29.9, importe_discrepante`

### 4. Gastos a Revisar

*   **Detalle:** Un gasto marcado para revisión de proveedor.
*   **Incidencia:**
    *   `2026-05-03, Suscripcion IA, software, 120.0, 120.0, revisar_proveedor`

## Recomendaciones de Control Interno

Para mitigar los riesgos identificados y fortalecer el control interno sobre los gastos, se proponen las siguientes recomendaciones:

1.  **Detección y Prevención de Duplicados:**
    *   **Acción:** Implementar un sistema automatizado de detección de duplicados que compare `fecha`, `concepto`, `categoría` e `importe` al momento de la carga.
    *   **Proceso:** Establecer un flujo de trabajo donde cualquier posible duplicado requiera revisión y aprobación manual antes de su procesamiento final.

2.  **Política de Recibos y Digitalización:**
    *   **Acción:** Reforzar la política de "no recibo, no reembolso" y comunicar claramente su obligatoriedad a todo el personal.
    *   **Proceso:** Explorar e implementar soluciones digitales (apps de gestión de gastos) que faciliten la carga y el almacenamiento de recibos de manera instantánea y segura.

3.  **Conciliación Automática de Importes:**
    *   **Acción:** Desarrollar o adquirir un sistema que realice una conciliación automática entre el `importe_declarado` y el `importe_esperado`.
    *   **Proceso:** Generar alertas automáticas para cualquier discrepancia, requiriendo una justificación detallada por parte del empleado y una aprobación gerencial antes de la liquidación.

4.  **Revisión Periódica de Proveedores:**
    *   **Acción:** Establecer un calendario para la revisión periódica de todos los proveedores y suscripciones, especialmente los recurrentes.
    *   **Proceso:** Asegurar que los servicios contratados sigan siendo necesarios, competitivos en precio y que los términos sean favorables para la organización.

5.  **Centralización y Auditorías Continuas:**
    *   **Acción:** Centralizar la gestión de todos los gastos en una única plataforma o sistema integrado.
    *   **Proceso:** Realizar auditorías internas aleatorias de gastos de forma mensual o trimestral para asegurar el cumplimiento constante de las políticas y procedimientos establecidos.
    *   **Capacitación:** Organizar sesiones de capacitación regulares para el personal sobre las políticas y procedimientos de gastos actualizados.
