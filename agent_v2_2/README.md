# Inspector Agent 2.2

Version autocontenida y portable del agente Inspector, reconstruida con
paridad operativa, routing por capacidades y control de cuota Codex.

Empieza por [`READ_FIRST.md`](READ_FIRST.md). Contiene el estado real, el orden
de lectura y el primer paso de reanudacion.

## Instalacion

```bash
cd agent_v2_2
pip install -e .
```

Copia `.env.example` a `.env` y rellena las claves necesarias.

## Arranque

```bash
agent-v2-2 start
```

## Comandos Telegram principales

- `estado`
- `diagnostico proveedores`
- `directorios`
- `añadir directorio D:\ruta`
- `quitar directorio D:\ruta`
- `recargar configuracion`
- `reiniciar agente`
- `cancelar operacion`
- `activar modo desarrollo` o `activar modo desarrollador`
- `iniciar bateria`, `prueba siguiente`, `repetir prueba`
