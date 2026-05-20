# Cruce de pagos y facturas

## Coincidencias

*   **Factura F-100:** Se detectó una coincidencia aproximada con un pago. La factura tiene un importe de 1210.00 y la fecha registrada es PHONE_0008. El pago asociado, con concepto "TRANSFERENCIA ACME F-100", tiene un importe de 125.00 y la fecha registrada es PHONE_0012. La discrepancia en el importe es significativa.

*   **Factura F-101:** Se detectó una coincidencia aproximada con un pago. La factura tiene un importe de 847.50 y la fecha registrada es PHONE_0007. El pago asociado, con concepto "ORG_0003 FACTURA 101", tiene un importe de 125.00 y la fecha registrada es PHONE_0010. La discrepancia en el importe es significativa.

## Discrepancias

*   **Factura F-102:** No se encontró ninguna coincidencia en los pagos registrados para la factura con importe 430.00 y fecha PHONE_0006.

*   **Factura sin número (ORG_0001):** Se encontró una entrada en el archivo de facturas que parece corresponder a una factura sin un identificador claro (ORG_0001), con un importe de 980.00 y fecha PHONE_0005. No se encontró una coincidencia directa en los pagos.

*   **Pago ORG_0005:** Se registró un pago con concepto "PAGO ORG_0005" por un importe de 125.00 y fecha PHONE_0009. No se pudo asociar directamente con ninguna factura específica en el archivo `facturas.csv`.

*   **Pago INGRESO VARIOS:** Se registró un pago con concepto "INGRESO VARIOS" por un importe de 125.00 y fecha PHONE_0009. No se pudo asociar directamente con ninguna factura específica en el archivo `facturas.csv`.
