import argparse
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_v2_2.cli")

def start_agent():
    logger.info("Iniciando Inspector Agent 2.2...")
    # TODO: Inicializar la configuración, base de datos y pasarela de Telegram
    print("El agente se ha iniciado (smoke test).")

def check_status():
    logger.info("Comprobando estado del sistema...")
    # TODO: Proveer diagnóstico rápido
    print("Estado: OK")

def main():
    parser = argparse.ArgumentParser(description="Inspector Agent 2.2 CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Start
    start_parser = subparsers.add_parser("start", help="Inicia el agente (Telegram long-polling)")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Comprueba el estado del agente y dependencias")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_agent()
    elif args.command == "status":
        check_status()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
