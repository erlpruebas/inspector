from __future__ import annotations
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent / "temp_bench_assets"

def create_assets():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. acta.txt
    (ASSETS_DIR / "acta.txt").write_text(
        "Reunión de Equipo del 15 de Mayo de 2026\n"
        "Asistentes: Ana, Marta, Juan\n"
        "Temas tratados:\n"
        "- Presupuesto: Aprobado el coste de licencias anuales de software.\n"
        "- Plazos: El proyecto de migración se retrasa al 1 de Julio.\n"
        "- Tareas urgentes:\n"
        "  1. Marta debe validar las tarifas de los servidores.\n"
        "  2. Juan creará la base de datos de staging.\n",
        encoding="utf-8"
    )
    
    # 2. ventas.csv
    (ASSETS_DIR / "ventas.csv").write_text(
        "Fecha,Producto,Cantidad,Precio,Total\n"
        "2026-05-01,Licencia A,2,100,200\n"
        "2026-05-02,Licencia B,1,250,250\n"
        "2026-05-03,Soporte,5,50,250\n"
        "2026-05-04,Licencia A,1,100,100\n",
        encoding="utf-8"
    )
    
    # 3. clientes.csv
    (ASSETS_DIR / "clientes.csv").write_text(
        "Nombre,Email,Telefono,Ciudad\n"
        "Luis Gomez,luis@mail.com,600111222,Madrid\n"
        "Ana Silva,ana@mail.com,600333444,Barcelona\n"
        "Pedro Perez,pedro@mail.com,600555666,Madrid\n"
        "Marta Sanz,marta@mail.com,600777888,Valencia\n",
        encoding="utf-8"
    )
    
    # 4. emails_sucios.txt
    (ASSETS_DIR / "emails_sucios.txt").write_text(
        "Hola, aquí tienes los contactos. Escríbele a juan.perez@empresa.com para facturas.\n"
        "Para soporte técnico contactar a support@service.org, o si no responde escribe a backup_admin@service.org.\n"
        "El correo personal de Marta es marta123@gmail.com. Gracias!\n",
        encoding="utf-8"
    )
    
    # 5. programa_roto.py
    (ASSETS_DIR / "programa_roto.py").write_text(
        "def calcular_cuadrado(numero):\n"
        "    return numero ** 2\n\n"
        "# ERROR DE SINTAXIS: Faltan dos puntos\n"
        "if calcular_cuadrado(5) > 10\n"
        "    print('Es mayor')\n",
        encoding="utf-8"
    )
    
    # 6. facturas.csv
    (ASSETS_DIR / "facturas.csv").write_text(
        "ID,Factura,Cliente,Total\n"
        "F01,FACT-1001,Luis Gomez,200\n"
        "F02,FACT-1002,Ana Silva,450\n"
        "F03,FACT-1003,Pedro Perez,120\n",
        encoding="utf-8"
    )
    
    # 7. pagos.csv
    (ASSETS_DIR / "pagos.csv").write_text(
        "PagoID,FacturaID,Monto,Estado\n"
        "P01,F01,200,Completado\n"
        "P02,F03,120,Completado\n",
        encoding="utf-8"
    )
    
    # 8. presupuesto_a.txt
    (ASSETS_DIR / "presupuesto_a.txt").write_text(
        "Presupuesto de Distribuidora A:\n"
        "Partida Hardware: Servidores Dell PowerEdge - Coste total: 4500 USD\n"
        "Partida Software: Licencias Windows Server - Coste: 1200 USD\n",
        encoding="utf-8"
    )
    
    # 9. presupuesto_b.txt
    (ASSETS_DIR / "presupuesto_b.txt").write_text(
        "Presupuesto de Distribuidora B:\n"
        "Partida Hardware: Servidores HP ProLiant - Coste total: 4100 USD\n"
        "Partida Software: Licencias Windows Server - Coste: 1400 USD\n",
        encoding="utf-8"
    )
    
    # 10. notas.txt
    (ASSETS_DIR / "notas.txt").write_text(
        "Notas del taller de producto:\n"
        "- Debemos migrar las cuentas antiguas de usuarios.\n"
        "- Responsable: Juan Gomez. Plazo: 10 de Junio.\n"
        "- Riesgo detectado: Caída temporal del servicio durante migración.\n",
        encoding="utf-8"
    )
    
    # 11. app.log
    (ASSETS_DIR / "app.log").write_text(
        "[2026-06-02 10:15:30] INFO System started\n"
        "[2026-06-02 10:20:00] ERROR Database Connection Failed - Host Unreachable\n"
        "[2026-06-02 10:20:05] ERROR Database Connection Failed - Attempt 2\n"
        "[2026-06-02 10:22:00] INFO Recovery successful\n",
        encoding="utf-8"
    )
    
    # 12. db.log
    (ASSETS_DIR / "db.log").write_text(
        "10:19:58 Connection open: user=admin\n"
        "10:20:00 Lost Connection to Database backend\n"
        "10:21:55 Database service rebooted\n"
        "10:22:00 Connection restored\n",
        encoding="utf-8"
    )
    
    # 13. alumnos.csv
    (ASSETS_DIR / "alumnos.csv").write_text(
        "AlumnoID,Nombre\n"
        "A01,Carlos Perez\n"
        "A02,Lucia Martinez\n"
        "A03,Sofia Torres\n",
        encoding="utf-8"
    )
    
    # 14. notas.csv
    (ASSETS_DIR / "notas.csv").write_text(
        "ID,Matematicas,Lengua\n"
        "A01,8.5,7.0\n"
        "A02,9.0,8.5\n"
        "A03,6.5,7.5\n",
        encoding="utf-8"
    )
    
    # 15. cuentas.xlsx (Guardamos como CSV para legibilidad del sandbox, pero con nombre cuentas.xlsx)
    # Codex CLI puede interpretar CSVs con extensión .xlsx si le decimos que es Excel o lo lee como csv
    (ASSETS_DIR / "cuentas.xlsx").write_text(
        "Concepto,Ingresos,Gastos\n"
        "Servicios Cloud,0,1500\n"
        "Licencias Software,0,800\n"
        "Consultoría Ventas,5000,0\n"
        "Mantenimiento,0,300\n",
        encoding="utf-8"
    )
    
    # 16. datos.txt
    (ASSETS_DIR / "datos.txt").write_text(
        "Resumen de Operación 2026:\n"
        "Ingresos Totales: 50000 EUR\n"
        "Gastos Totales: 35000 EUR\n"
        "Beneficio Neto: 15000 EUR\n",
        encoding="utf-8"
    )
    
    print("Assets de prueba creados en:", ASSETS_DIR)

if __name__ == "__main__":
    create_assets()
