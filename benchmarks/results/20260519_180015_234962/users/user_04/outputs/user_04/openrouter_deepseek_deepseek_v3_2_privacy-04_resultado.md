# Resultado del cruce de pagos y facturas

## Coincidencias encontradas

**1. Factura F-100 (1210.00)**
- **Pago coincidente**: TRANSFERENCIA ACME F-100 (1210.00)
- **Estado**: Coincidencia exacta en importe
- **Nota**: La referencia en el concepto del pago incluye "F-100", confirmando la relación

**2. Factura F-101 (847.50)**
- **Pago coincidente**: ORG_0003 FACTURA 101 (847.50)
- **Estado**: Coincidencia exacta en importe
- **Nota**: La referencia en el concepto del pago incluye "FACTURA 101", confirmando la relación

## Discrepancias detectadas

**1. Factura F-102 (430.00)**
- **Estado**: Sin pago coincidente
- **Observación**: No existe ningún pago por importe de 430.00

**2. Factura sin referencia (980.00)**
- **Estado**: Sin pago coincidente
- **Observación**: Factura sin identificador claro (posible error en datos) por 980.00 sin pago correspondiente

**3. Pagos sin factura asociada:**
- **PAGO ORG_0005 (125.00)**: No existe factura por este importe
- **INGRESO VARIOS (125.00)**: No existe factura por este importe

## Resumen
- **Facturas con pago**: 2 de 4 (50%)
- **Facturas pendientes**: 2 de 4 (50%)
- **Pagos sin factura clara**: 2 de 4 (
