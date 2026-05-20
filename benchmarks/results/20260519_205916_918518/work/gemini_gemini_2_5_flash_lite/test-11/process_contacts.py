import csv
from collections import defaultdict
import io

# Define the input CSV file path
csv_file_path = "assistant_synthetic/contactos_50.csv"
output_file_path = "resultado.md"

data = []
try:
    # Directly read from the provided CSV file
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        data = list(csv_reader)
except FileNotFoundError:
    print(f"Error: The file {csv_file_path} was not found.")
    exit()
except Exception as e:
    print(f"Error reading CSV file: {e}")
    exit()

# Filter for high priority clients
high_priority_clients = [client for client in data if client.get('prioridad') == 'alta']

# Group by city
clients_by_city = defaultdict(list)
for client in high_priority_clients:
    clients_by_city[client.get('ciudad')].append(client)

# Define business actions
def get_business_actions(city):
    return [
        f"Offer exclusive early access to new products in {city}.",
        f"Develop a loyalty program with special discounts for clients in {city}.",
        f"Organize a networking event for high-priority clients in {city} to foster stronger relationships."
    ]

# Generate output content in Markdown format
output_content = """# Clientes de Alta Prioridad y Acciones Comerciales

"""

for city, clients in clients_by_city.items():
    output_content += f"""
## {city}

"""
    output_content += f"""
Clientes de alta prioridad ({len(clients)}):
"""
    for client in clients:
        company_name = client.get('empresa') or client.get('nombre')
        output_content += f"""
- {client.get('nombre')} ({company_name})
"""

    output_content += """
Acciones Comerciales Recomendadas:
"""
    actions = get_business_actions(city)
    for i, action in enumerate(actions):
        output_content += f"""
{i+1}. {action}
"""
    output_content += """
"""

# Write to output file
try:
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(output_content)
    print(f"Processed data and saved results to {output_file_path}")
except Exception as e:
    print(f"Error writing to output file {output_file_path}: {e}")
