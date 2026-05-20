
import csv
import io
from collections import defaultdict
import os

# File paths for each month's data
file_paths = {
    "Enero": "assistant_synthetic/gastos_2026_01.csv",
    "Febrero": "assistant_synthetic/gastos_2026_02.csv",
    "Marzo": "assistant_synthetic/gastos_2026_03.csv",
    "Abril": "assistant_synthetic/gastos_2026_04.csv",
    "Mayo": "assistant_synthetic/gastos_2026_05.csv",
}

monthly_summary = {}
category_summary = defaultdict(lambda: defaultdict(float))
anomalies = defaultdict(list)

for month, file_path in file_paths.items():
    monthly_total = 0.0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    importe = float(row['importe_declarado'])
                    monthly_total += importe
                    
                    category = row['categoria']
                    category_summary[month][category] += importe
                    
                    if row['estado'] != 'ok':
                        anomalies[month].append({
                            "concepto": row['concepto'],
                            "categoria": category,
                            "importe": importe,
                            "estado": row['estado']
                        })
                except ValueError:
                    # Silently skip if importe_declarado is not a valid float
                    pass 
                except KeyError as e:
                    print(f"Missing key in row: {e} - {row} in file {file_path}") # Log missing keys

        monthly_summary[month] = monthly_total

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

# Prepare the output content
output_lines = []
output_lines.append("# Resumen Financiero de Gastos (Enero - Mayo 2026)")
output_lines.append("") # Blank line after title

# Monthly Totals
output_lines.append("## Totales por Mes")
output_lines.append("")
for month, total in sorted(monthly_summary.items(), key=lambda item: list(file_paths.keys()).index(item[0])):
    output_lines.append(f"- **{month}**: ${total:.2f}")
output_lines.append("") # Blank line after monthly totals

# Top Categories per Month
output_lines.append("## Gastos por Categoría (por Mes)")
output_lines.append("")
for month, categories in sorted(category_summary.items(), key=lambda item: list(file_paths.keys()).index(item[0])):
    output_lines.append(f"### {month}")
    sorted_categories = sorted(categories.items(), key=lambda item: item[1], reverse=True)
    for category, amount in sorted_categories:
        output_lines.append(f"- **{category}**: ${amount:.2f}")
    output_lines.append("") # Blank line after each month's categories

# Anomalies
output_lines.append("## Lista de Anomalías")
output_lines.append("")
for month, anomaly_list in sorted(anomalies.items(), key=lambda item: list(file_paths.keys()).index(item[0])):
    if anomaly_list:
        output_lines.append(f"### {month}")
        for anomaly in anomaly_list:
            output_lines.append(f"- **Concepto**: {anomaly['concepto']}, **Categoría**: {anomaly['categoria']}, **Importe**: ${anomaly['importe']:.2f}, **Estado**: {anomaly['estado']}")
        output_lines.append("") # Blank line after each month's anomalies

output_content = "
".join(output_lines)

# Write to file
output_file_path = "resultado.md"
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(output_content)

print(f"Financial summary generated and saved to {output_file_path}")
