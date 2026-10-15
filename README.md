# Rail Yard: inspección circular de vagones

Aplicación didáctica para el taller de **listas doblemente circulares**. Modela la composición de un patio de carga y permite administrar sus vagones desde una interfaz web; la lógica de la estructura está implementada en Python y no requiere dependencias externas.

## Caso de estudio

Los patios ferroviarios gestionan vagones de carga que deben identificarse, agruparse por composición y revisarse durante las operaciones. En este simulador, el personal puede recorrer repetidamente los vagones asignados a una ronda de inspección, avanzar o retroceder para revisar un elemento y registrar o retirar vagones cuando cambia la composición.

El caso se aplica a una actividad realista de patio ferroviario, pero **la aplicación es un simulador académico**: no está conectada a una compañía ferroviaria y sus vagones iniciales, cargas, pesos y destinos son datos ficticios. Los vagones físicos de un tren no forman un círculo; la circularidad representa el recorrido repetible del sistema de inspección, que pasa del último elemento al primero y viceversa.

Como referencia del contexto operativo, la [Parte 215 del título 49 del CFR](https://www.ecfr.gov/current/title-49/subtitle-B/chapter-II/part-215) establece estándares de seguridad para vagones ferroviarios de carga. La aplicación no implementa ni certifica esas inspecciones reglamentarias; usa la gestión del patio como escenario pedagógico para estudiar la estructura de datos.

### ¿Por qué una lista doblemente circular?

Cada vagón se almacena en un nodo con enlaces `next` y `previous`. El último nodo apunta al primero y el primero al último. Así, una ronda puede continuar sin reiniciar manualmente el recorrido y el operador puede invertir la dirección de inspección en cualquier momento.

| Operación | Complejidad | Uso en la aplicación |
| --- | --- | --- |
| Avanzar / retroceder | O(1) | Mover el vagón seleccionado en el circuito |
| Buscar / retirar por código | O(n) | Localizar el vagón que se desea quitar |
| Añadir al final | O(n) | Evitar códigos duplicados antes de enlazar el nuevo nodo |
| Recorrer todos los vagones | O(n) | Dibujar la composición y calcular el peso total |

El enlace de un nuevo nodo al final y la eliminación de un nodo conocido son O(1); la operación pública de alta y baja busca el código para comprobar unicidad o encontrar el elemento, por eso su coste total es O(n).

## Funcionalidades

- Visualizar la composición como vagones enlazados y ver el nodo seleccionado.
- Avanzar y retroceder con comportamiento circular.
- Seleccionar un vagón directamente desde la vista del circuito.
- Registrar vagones al final con código único, carga, destino y peso.
- Retirar el vagón seleccionado.
- Consultar cantidad de vagones y peso acumulado.
- Recibir validaciones y errores en la interfaz sin usar la consola como interacción.

## Requisitos

- Python 3.10 o posterior.
- Navegador web moderno.

No se instalan paquetes: el servidor HTTP, la estructura de datos y las pruebas usan únicamente la biblioteca estándar de Python.

## Ejecución

Desde la raíz del proyecto:

```powershell
py -m trainyard.http_server
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000). El servidor escucha solo en la interfaz local. Detén la aplicación con `Ctrl+C`.

## Pruebas

```powershell
py -m unittest discover -s tests -v
```

Las pruebas verifican enlaces circulares, navegación en ambas direcciones, inserción, eliminación, casos vacíos, validación y las rutas principales de la API.

## Organización del proyecto

```text
trainyard/
  circular_list.py   Estructura de lista doblemente circular
  http_server.py     Servidor HTTP y API JSON
  models.py          Modelo y validación de cada vagón
web/
  index.html         Interfaz semántica en español
  static/
    app.js           Interacción con la API y renderizado del circuito
    styles.css       Diseño adaptable a escritorio y móvil
tests/
  test_circular_list.py
  test_http_server.py
```

## API local

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/api/wagons` | Composición, vagón actual, cantidad y peso total |
| `POST` | `/api/wagons` | Añade un vagón usando JSON |
| `DELETE` | `/api/wagons/{wagon_id}` | Retira un vagón por su código |
| `POST` | `/api/navigation/next` | Avanza al siguiente vagón |
| `POST` | `/api/navigation/previous` | Retrocede al vagón anterior |
| `GET` | `/api/health` | Comprueba que el servidor está activo |

Ejemplo de alta:

```json
{
  "wagon_id": "FC-420",
  "cargo": "Acero",
  "destination": "Terminal Central",
  "weight_tonnes": 42.5
}
```

El alta devuelve `409 Conflict` cuando el código ya existe y `400 Bad Request` ante datos inválidos. El peso debe ser positivo; el código, el tipo de carga y el destino no pueden estar vacíos.

## Flujo de la estructura

1. Al iniciar, se crean cuatro vagones de demostración y el primero queda seleccionado.
2. Cada nuevo vagón se enlaza entre la cola actual y la cabeza: `tail.next = nuevo`, `nuevo.previous = tail`, `nuevo.next = head` y `head.previous = nuevo`.
3. La navegación sigue el enlace correspondiente. Como los extremos están conectados, el movimiento nunca se detiene en el borde del circuito.
4. Al retirar el nodo actual, el siguiente queda seleccionado. Al retirar el último nodo, cabeza, cola y selección vuelven a `None`.
