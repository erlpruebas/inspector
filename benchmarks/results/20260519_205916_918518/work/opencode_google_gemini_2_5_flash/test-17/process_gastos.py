import pandas as pd
import glob
import os

def generate_financial_summary(input_dir, output_file):
    all_files = glob.glob(os.path.join(input_dir, "gastos_2026_*.csv"))
    
    df_list = []
    for f in all_files:
        df = pd.read_csv(f)
        df_list.append(df)
    
    full_df = pd.concat(df_list, ignore_index=True)
    
    # Convert 'fecha' to datetime and extract month
    full_df['fecha'] = pd.to_datetime(full_df['fecha'], errors='coerce')
    full_df['mes'] = full_df['fecha'].dt.strftime('%Y-%m')
    
    # Calculate monthly totals
    monthly_totals = full_df.groupby('mes')['importe_declarado'].sum().reset_index()
    monthly_totals = monthly_totals.sort_values('mes')
    
    # Calculate main category totals
    category_totals = full_df.groupby('categoria')['importe_declarado'].sum().reset_index()
    category_totals = category_totals.sort_values('importe_declarado', ascending=False)
    
    # Identify anomalies
    # Anomaly definition: expense > mean + 2*std in its category
    anomalies = []
    for category in full_df['categoria'].unique():
        category_df = full_df[full_df['categoria'] == category]
        if len(category_df) > 1: # Need at least 2 data points for std dev
            mean_expense = category_df['importe_declarado'].mean()
            std_expense = category_df['importe_declarado'].std()
            
            # Filter for declared_amount > mean + 2*std
            # Using absolute value for 'importe_declarado' to catch both extremely high and low anomalies
            # For this benchmark, we only care about high expenses so we'll only check the upper bound
            
            anomalous_expenses = category_df[category_df['importe_declarado'] > (mean_expense + 2 * std_expense)]
            if not anomalous_expenses.empty:
                for index, row in anomalous_expenses.iterrows():
                    anomalies.append({
                        'fecha': row['fecha'].strftime('%Y-%m-%d') if pd.notna(row['fecha']) else 'N/A',
                        'concepto': row['concepto'],
                        'categoria': row['categoria'],
                        'importe_declarado': row['importe_declarado']
                    })
        elif len(category_df) == 1:
            # If there's only one expense in a category, it can't be anomalous relative to itself
            pass

    # Generate Markdown output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Resumen financiero de gastos enero-mayo

")
        f.write("## Total por mes
")
        for index, row in monthly_totals.iterrows():
            f.write(f"- {row['mes']}: {row['importe_declarado']:.2f} EUR
")
        
        f.write("
## Categorías principales
")
        for index, row in category_totals.iterrows():
            f.write(f"- {row['categoria']}: {row['importe_declarado']:.2f} EUR
")
            
        f.write("
## Lista de anomalías (gastos > media + 2*desviación estándar por categoría)
")
        if anomalies:
            for anomaly in anomalies:
                f.write(f"- Fecha: {anomaly['fecha']}, Concepto: {anomaly['concepto']}, Categoría: {anomaly['categoria']}, Importe: {anomaly['importe_declarado']:.2f} EUR
")
        else:
            f.write("No se encontraron anomalías significativas.
")

if __name__ == "__main__":
    input_directory = "D:\inspector\benchmarks\results\20260519_205916_918518\work\opencode_google_gemini_2_5_flash\test-17\assistant_synthetic"
    output_filename = "D:\inspector\benchmarks\results\20260519_205916_918518\work\opencode_google_gemini_2_5_flash\test-17\resultado.md"
    generate_financial_summary(input_directory, output_filename)
