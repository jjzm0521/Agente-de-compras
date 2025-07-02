# Agente IA para Plan de Compra Personalizado

Este proyecto tiene como objetivo desarrollar un agente de Inteligencia Artificial capaz de convertir "wishlists" de redes sociales (Instagram, Pinterest) y carritos de compra abandonados en un plan de compra personalizado. Este plan busca incentivar ventas adicionales en marketplaces asociados y ayudar a los usuarios a encontrar productos según sus necesidades y presupuesto.

## Propuesta de Valor

-   **Para Usuarios**:
    -   Transforma la acumulación de productos guardados en un plan de acción.
    -   Ayuda a planificar compras según presupuesto y prioridades.
    -   Ofrece alertas de ofertas relevantes.
    -   Facilita la transición de la inspiración a la compra.
    -   Permite buscar productos según necesidades y presupuesto.

-   **Para Retailers**:
    -   Incrementa el valor promedio de orden (AOV) mediante ventas cruzadas y bundles.
    -   Reduce el abandono de carritos con recordatorios contextuales.
    -   Proporciona datos enriquecidos sobre las preferencias sociales de los usuarios.

## Alcance y Funcionalidades Implementadas (Demostración Actual)

La demostración actual utiliza datos simulados (archivos JSON en la carpeta `data/`) para mostrar el siguiente flujo:

1.  **Ingesta de Datos**:
    *   Carga productos de un catálogo de marketplace (`marketplace_products.json`).
    *   Carga elementos guardados por un usuario en Instagram (`instagram_saves.json`).
    *   Carga pines de tableros de Pinterest (`pinterest_boards.json`).
    *   Carga carritos de compra abandonados (`abandoned_carts.json`).
2.  **Procesamiento Inicial**:
    *   Identifica una lista de deseos inicial del usuario a partir de las fuentes anteriores.
3.  **Matching y Enriquecimiento de Productos**:
    *   Intenta hacer coincidir los productos de la lista de deseos con el catálogo del marketplace.
    *   Enriquece los productos de la lista de deseos con detalles del marketplace como precio, stock, etc.
4.  **Generación de Plan de Compra Personalizado**:
    *   Basado en la lista de deseos enriquecida y un presupuesto de usuario simulado (definido en `src/main.py`).
    *   Prioriza artículos de carritos abandonados.
    *   Sugiere artículos para comprar y otros para considerar más tarde si exceden el presupuesto o no están en stock.
5.  **Búsqueda de Productos**:
    *   Permite al usuario (simulado en `src/main.py`) buscar productos en el catálogo del marketplace según:
        *   Texto (nombre, descripción, etiquetas).
        *   Categoría.
        *   Marca.
        *   Rango de precios.
        *   Rating mínimo.
        *   Disponibilidad en stock.

## Tecnologías Clave

-   **Python 3.9+**
-   **LangGraph**: Para orquestar el flujo de procesamiento del agente mediante un grafo de estados.
-   **Manejo de Datos**: Archivos JSON para simular bases de datos y entradas de usuario.
-   **Pruebas Unitarias**: Módulo `unittest` de Python.

## Estructura del Repositorio

```
.
├── data/                 # Datos simulados (JSON, CSV)
│   ├── instagram_saves.json
│   ├── pinterest_boards.json
│   ├── marketplace_products.json
│   └── abandoned_carts.json
├── src/                  # Código fuente del agente
│   ├── agent/            # Lógica del agente (LangGraph)
│   ├── integrations/     # Módulos para interactuar con fuentes de datos
│   ├── utils/            # Funciones de utilidad
│   └── main.py           # Punto de entrada o script de demostración
├── tests/                # Pruebas unitarias y de integración
├── README.md             # Este archivo
└── AGENTS.md             # Directrices para el desarrollo con IA
```

## Cómo Ejecutar

### Requisitos Previos
Asegúrate de tener Python 3.9 o superior instalado.

### Instalación de Dependencias
Las dependencias principales son `langgraph` y `langchain`. Puedes instalarlas junto con otras necesarias para el proyecto:
```bash
pip install langgraph langchain langchain_core
# Para la visualización del grafo (opcional, requiere Graphviz instalado en el sistema):
# pip install pygraphviz
```
(Nota: `pygraphviz` puede tener dependencias de sistema que necesitan ser instaladas primero, como `graphviz` mismo. Consulta la documentación de `pygraphviz`.)

### Ejecutar la Demostración Principal
El script principal `src/main.py` ejecuta todo el flujo del agente, incluyendo la carga de datos, generación del plan de compra y una búsqueda de productos simulada.
Para ejecutarlo desde la raíz del repositorio:
```bash
python -m src.main
```
Esto mostrará en la consola los pasos que el agente está realizando y los resultados finales, incluyendo el plan de compra y los resultados de la búsqueda.

### Ejecutar las Pruebas Unitarias
Para ejecutar las pruebas unitarias, navega a la raíz del repositorio y ejecuta:
```bash
python -m unittest discover -s tests -v
```
Esto descubrirá y correrá todas las pruebas definidas en la carpeta `tests/`.

## Flujo de la Demostración (`src/main.py`)

1.  **Inicialización**: Se crea el grafo del agente y se define un estado inicial (incluyendo un presupuesto simulado para el usuario).
2.  **Primera Invocación del Grafo (Plan de Compra)**:
    *   Se cargan todos los datos de las fuentes simuladas (marketplace, Instagram, Pinterest, carritos).
    *   Se procesan estos datos para identificar una lista de deseos.
    *   Los productos de la lista de deseos se comparan y enriquecen con el catálogo del marketplace.
    *   Se genera un plan de compra inicial basado en el presupuesto y la disponibilidad.
    *   El nodo de búsqueda de productos se ejecuta (sin criterios aún), indicando que no se proporcionaron criterios.
3.  **Simulación de Búsqueda de Productos**:
    *   Se establecen criterios de búsqueda simulados en el estado del agente (ej: buscar "cafetera" con un precio máximo).
4.  **Segunda Invocación del Grafo (Búsqueda)**:
    *   El grafo se invoca nuevamente con el estado actualizado. **Importante**: En esta demo, esto significa que los nodos de carga y procesamiento inicial se ejecutan de nuevo. En una aplicación más compleja, se optimizaría este flujo para evitar trabajo redundante.
    *   El nodo de búsqueda de productos ahora utiliza los criterios proporcionados para filtrar los productos del marketplace.
5.  **Resultados Finales**:
    *   Se imprime un resumen completo del estado final del agente, incluyendo los datos cargados, el plan de compra generado y los resultados de la búsqueda de productos.

## Próximos Pasos (Plan General)

Consultar el plan activo del agente IA para los detalles. También se pueden considerar los siguientes puntos para futuras mejoras:
-   Mejorar el algoritmo de matching de productos (ej. usando embeddings o técnicas de NLP más avanzadas).
-   Refinar la lógica de priorización del plan de compra.
-   Implementar una interfaz de usuario (CLI o web básica) en lugar de simular la interacción en `main.py`.
-   Conectar con APIs reales de redes sociales y marketplaces (considerando políticas de acceso y privacidad).
-   Añadir persistencia para el estado del agente o los perfiles de usuario.
-   Optimizar el flujo del grafo para evitar la re-ejecución innecesaria de nodos.
