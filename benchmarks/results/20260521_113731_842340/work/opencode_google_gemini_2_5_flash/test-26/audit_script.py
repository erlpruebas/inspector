
import pandas as pd
import os

def run_audit():
    # Define the directory and file pattern
    base_dir = "D:\\inspector\\benchmarks\\results\\20260521_113731_842340\\work\\opencode_google_gemini_2_5_flash\\test-26"
    data_dir = os.path.join(base_dir, "assistant_synthetic")
    file_pattern = "gastos_2026_0*.csv"

    all_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.startswith("gastos_2026_") and f.endswith(".csv")]
    all_files.sort() # Ensure consistent order

    df_list = []
    for f in all_files:
        df = pd.read_csv(f)
        df_list.append(df)

    if not df_list:
        with open(os.path.join(base_dir, "resultado.md"), "w") as f:
            f.write("# Auditoría de Gastos

No se encontraron archivos de gastos para auditar.
")
        return

    combined_df = pd.concat(df_list, ignore_index=True)

    # Convert 'fecha' to datetime
    combined_df['fecha'] = pd.to_datetime(combined_df['fecha'])

    # Sort by date
    combined_df = combined_df.sort_values(by='fecha')

    # --- Audit Checks ---

    # 1. Duplicados
    # A duplicate is defined by same date, concept, category, and declared amount.
    duplicates = combined_df[combined_df.duplicated(subset=['fecha', 'concepto', 'categoria', 'importe_declarado'], keep=False)]

    # 2. Recibos faltantes (assuming 'estado' != 'ok' means missing receipt)
    missing_receipts = combined_df[combined_df['estado'] != 'ok']

    # 3. Discrepancias (importe_declarado != importe_esperado)
    discrepancies = combined_df[combined_df['importe_declarado'] != combined_df['importe_esperado']]

    # --- Generate Report ---
    report_content = "# Auditoría Completa de Gastos (Enero - Mayo 2026)

"
    report_content += "Este informe presenta los hallazgos de la auditoría de gastos de enero a mayo de 2026, junto con recomendaciones de control interno.

"
    report_content += "## Resumen General

"
    report_content += f"- Total de transacciones auditadas: {len(combined_df)}
"
    report_content += f"- Número de transacciones duplicadas encontradas: {len(duplicates)}
"
    report_content += f"- Número de transacciones con recibos faltantes/pendientes: {len(missing_receipts)}
"
    report_content += f"- Número de transacciones con discrepancias de importe: {len(discrepancies)}

"

    if not duplicates.empty:
        report_content += "## Hallazgos: Transacciones Duplicadas

"
        report_content += "Se encontraron las siguientes transacciones que parecen ser duplicados (misma fecha, concepto, categoría e importe declarado):

"
        report_content += duplicates.to_markdown(index=False) + "

"
    else:
        report_content += "## Hallazgos: Transacciones Duplicadas

No se encontraron transacciones duplicadas.

"

    if not missing_receipts.empty:
        report_content += "## Hallazgos: Recibos Faltantes o Pendientes

"
        report_content += "Las siguientes transacciones tienen un estado diferente a 'ok', indicando un posible recibo faltante o pendiente:

"
        report_content += missing_receipts.to_markdown(index=False) + "

"
    else:
        report_content += "## Hallazgos: Recibos Faltantes o Pendientes

No se encontraron transacciones con recibos faltantes o pendientes.

"

    if not discrepancies.empty:
        report_content += "## Hallazgos: Discrepancias en Importes

"
        report_content += "Las siguientes transacciones muestran una diferencia entre el 'importe_declarado' y el 'importe_esperado':

"
        report_content += discrepancies.to_markdown(index=False) + "

"
    else:
        report_content += "## Hallazgos: Discrepancias en Importes

No se encontraron discrepancias entre el importe declarado y el esperado.

"

    report_content += "## Recomendaciones de Control Interno

"
    report_content += "Para mitigar los riesgos identificados y mejorar la gestión de gastos, se proponen las siguientes recomendaciones:

"
    report_content += "1.  **Detección de Duplicados:** Implementar un sistema automatizado que compare transacciones nuevas con registros existentes basándose en `fecha`, `concepto`, `categoría` e `importe_declarado` antes de la aprobación final. Esto puede incluir alertas o bloqueos automáticos para transacciones sospechosas.
"
    report_content += "2.  **Gestión de Recibos:** Establecer un proceso estricto para la presentación y verificación de recibos. Esto podría incluir:
"
    report_content += "    *   Plazos definidos para la entrega de recibos después de la transacción.
"
    report_content += "    *   Un sistema de carga digital de recibos que vincule automáticamente el recibo a la transacción.
"
    report_content += "    *   Un seguimiento proactivo de recibos pendientes con recordatorios automáticos.
"
    report_content += "3.  **Conciliación de Importes:** Asegurar que los importes declarados y esperados sean revisados y conciliados por una segunda persona o un sistema automatizado. Cualquier discrepancia debe ser investigada y justificada antes de la aprobación del gasto.
"
    report_content += "4.  **Auditorías Periódicas:** Realizar auditorías internas regulares, al menos trimestrales, para identificar patrones de fraude o error que los controles diarios podrían pasar por alto. Esto incluye la revisión de un muestreo de transacciones completas.
"
    report_content += "5.  **Capacitación Continua:** Proporcionar capacitación continua a los empleados sobre las políticas de gastos, la importancia de la precisión en la declaración y las consecuencias del incumplimiento.
"
    report_content += "6.  **Estandarización de Categorías y Conceptos:** Utilizar un catálogo estandarizado de categorías y conceptos de gasto para minimizar errores de clasificación y facilitar la detección de anomalías.
"
    report_content += "7.  **Separación de Funciones:** Asegurar que las responsabilidades de autorización, registro y conciliación de gastos estén separadas entre diferentes individuos o departamentos para evitar conflictos de interés y reducir el riesgo de fraude.
"

    # Write the report to resultado.md
    with open(os.path.join(base_dir, "resultado.md"), "w", encoding="utf-8") as f:
        f.write(report_content)

if __name__ == "__main__":
    run_audit()
