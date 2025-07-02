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
-   **Langchain & LangGraph**: Para construir el agente y orquestar el flujo de procesamiento mediante un grafo de estados. Se utilizan componentes de Langchain como `ChatPromptTemplate` y modelos Pydantic para la interacción con LLMs.
-   **Langchain-OpenAI**: Para la integración con modelos de lenguaje de OpenAI (como GPT-4o Mini).
-   **OpenAI API**: Necesaria para las funcionalidades de Inteligencia Artificial (análisis de wishlist, generación de consejos).
-   **Manejo de Datos**: Archivos JSON para simular bases de datos y entradas de usuario.
-   **Python-Dotenv**: Para gestionar la API key de OpenAI de forma segura mediante archivos `.env`.
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
Las dependencias principales incluyen `langgraph`, `langchain`, `langchain-openai` y `python-dotenv`. Puedes instalarlas (idealmente en un entorno virtual):
```bash
pip install langgraph langchain langchain_core langchain-openai python-dotenv
# Para la visualización del grafo (opcional, requiere Graphviz instalado en el sistema):
# pip install pygraphviz # Puede tener dependencias de sistema como graphviz.
```

### Configuración de la API Key de OpenAI
**Este paso es crucial para que funcionen las características de Inteligencia Artificial.**

1.  **Copia el archivo de ejemplo**: En la raíz del proyecto, encontrarás un archivo llamado `.env.example`. Copia este archivo y renombra la copia a `.env`.
2.  **Edita el archivo `.env`**: Abre el archivo `.env` con un editor de texto.
3.  **Añade tu API Key**: Modifica la línea `OPENAI_API_KEY="sk-tu_api_key_aqui"` reemplazando `"sk-tu_api_key_aqui"` con tu API Key real de OpenAI.
4.  **Modelo (Opcional)**: Puedes especificar el modelo de OpenAI en la línea `OPENAI_MODEL_NAME="gpt-4o-mini"`. Si esta línea no existe o está comentada, el sistema usará "gpt-4o-mini" por defecto para las nuevas funcionalidades de IA.

El archivo `.env` está incluido en `.gitignore`, por lo que tu API key no se compartirá si subes el código a un repositorio Git.

Si no configuras la API Key, el programa se ejecutará, pero las funcionalidades de IA (análisis de wishlist, consejos de compra) mostrarán un error indicando que la API Key no fue encontrada y no podrán operar.

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

1.  **Inicialización**: Se crea el grafo del agente y se define un estado inicial (incluyendo un presupuesto simulado y campos para los resultados de la IA).
2.  **Primera Invocación del Grafo (Flujo Principal del Agente)**:
    *   **Carga de Datos**: Se cargan todos los datos de las fuentes simuladas (marketplace, Instagram, Pinterest, carritos).
    *   **Análisis de Wishlist con IA (WishlistAgent)**:
        *   Los items de Instagram y Pinterest son analizados por un LLM (GPT-4o Mini o el configurado) para extraer nombre del producto, categoría, características y sentimiento del usuario.
        *   Si la API Key de OpenAI no está configurada, este paso reportará un error y la wishlist analizada por IA estará vacía.
    *   **Extracción de Datos de Carrito**: Los items de carritos abandonados se procesan para un matching directo por ID.
    *   **Matching y Enriquecimiento de Productos**:
        *   Los productos de la wishlist analizada por IA se intentan hacer coincidir con el catálogo del marketplace, usando el nombre y la categoría identificados por la IA para mejorar la precisión.
        *   Los items de carritos se machean directamente por su ID de producto.
        *   Todos los items macheados se enriquecen con detalles del marketplace (precio, stock, etc.).
    *   **Generación de Plan de Compra (ShoppingPlannerAgent)**:
        *   Se genera un plan de compra basado en la wishlist enriquecida y el presupuesto.
        *   **Consejos de Compra con IA**: Para los primeros items del plan, se intenta usar el LLM para generar consejos de compra personalizados. Si la API Key no está configurada, no se generarán consejos.
    *   **Búsqueda de Productos (Inicial)**: El nodo de búsqueda se ejecuta (sin criterios inicialmente), indicando que no se proporcionaron criterios.
3.  **Simulación de Búsqueda de Productos (Segunda Parte del Flujo en `main.py`)**:
    *   Se establecen criterios de búsqueda simulados en el estado del agente (ej: buscar "cafetera" con un precio máximo).
4.  **Segunda Invocación del Grafo (para la Búsqueda)**:
    *   El grafo se invoca nuevamente con el estado actualizado. **Importante**: En esta demo, esto significa que los nodos anteriores (incluyendo las llamadas a IA) se ejecutan de nuevo. En una aplicación más compleja, se optimizaría este flujo.
    *   El nodo de búsqueda de productos ahora utiliza los criterios proporcionados para filtrar los productos del marketplace.
5.  **Resultados Finales**:
    *   Se imprime un resumen completo del estado final del agente:
        *   Errores del WishlistAgent (si los hubo).
        *   Un resumen de la wishlist analizada por IA.
        *   El plan de compra, incluyendo los consejos de IA si se generaron.
        *   Los resultados de la búsqueda de productos.

## Próximos Pasos (Plan General)

Consultar el plan activo del agente IA para los detalles. Mejoras futuras podrían incluir:
-   Mejorar el algoritmo de matching de productos (ej. usando embeddings o técnicas de NLP más avanzadas).
-   Refinar la lógica de priorización del plan de compra.
-   Implementar una interfaz de usuario (CLI o web básica) en lugar de simular la interacción en `main.py`.
-   Conectar con APIs reales de redes sociales y marketplaces (considerando políticas de acceso y privacidad).
-   Añadir persistencia para el estado del agente o los perfiles de usuario.
-   Optimizar el flujo del grafo para evitar la re-ejecución innecesaria de nodos.
