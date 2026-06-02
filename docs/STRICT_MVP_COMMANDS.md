# Strict Telegram MVP

El MVP estricto evita que el router tenga que adivinar. Si el mensaje empieza por uno de estos comandos, el orquestador toma esa ruta exacta.

## Comandos activos

### `alarma texto`

Crea una alarma o recordatorio temporal.

Ejemplos:

```text
alarma avisame dentro de 15 minutos de revisar el horno
alarma recuerdame manana a las 9 llamar al taller
```

### `memoria texto`

Guarda el texto en el archivo de memoria con timestamp y no ejecuta nada mas.

Ejemplo:

```text
memoria para el ron anejo quiero calcular la cantidad exacta de caramelo por litro
```

### `recuerdo texto`

Busca en recuerdos y eventos. Si Gemini esta disponible, sintetiza una respuesta breve usando solo la memoria recuperada.

Ejemplo:

```text
recuerdo caramelo ron anejo
```

### `escritorio texto`

Fuerza Codex Desktop.

Ejemplo:

```text
escritorio abre una conversacion nueva y revisa el estado visual de la app
```

### `linea texto`

Fuerza Codex CLI.

Ejemplo:

```text
linea revisa los tests del orquestador y dime que falla
```

### `hilo actual`

Muestra el hilo activo.

### `nuevo hilo nombre`

Crea y activa un hilo nuevo.

### `usar hilo nombre`

Cambia al hilo indicado.

### `estado`

Muestra actividad actual, hilo y cola.

### `pendientes`

Lista tareas Codex pendientes.

### `siguiente`

Pide confirmacion para ejecutar la siguiente tarea pendiente.

## Tareas pendientes del MVP

- Normalizar acentos y variantes sin ampliar demasiado el parser.
- Separar memoria corta de eventos tecnicos para que `recuerdo` no mezcle ruido operativo.
- Crear tests automatizados de intencion para cada comando estricto.
- Definir politica de confirmacion: Codex CLI/Desktop con confirmacion, memoria y alarma sin confirmacion.
- Crear un comando `modelo ...` que lance `model_probe` desde Telegram cuando lo tengamos maduro.
