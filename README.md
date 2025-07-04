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

## Arquitectura del Agente (Evolucionando)

Este proyecto está evolucionando hacia una **arquitectura conversacional multi-agente** utilizando LangGraph. El objetivo es tener:

1.  Un **`ConversationalMasterAgent`**: Actúa como el orquestador principal, interactuando con el usuario en lenguaje natural, interpretando sus intenciones y delegando tareas a agentes especializados.
2.  **Agentes Especializados**: Módulos enfocados en tareas específicas (ej: analizar wishlists, buscar en catálogo, planificar compras, descubrir productos). Estos se están refactorizando para funcionar como "herramientas" que el `ConversationalMasterAgent` puede invocar.

Actualmente, se ha implementado un **esqueleto mejorado del `ConversationalMasterAgent`**. Este agente ahora:
-   Establece un bucle de chat básico en la línea de comandos (CLI).
-   Intenta usar un Modelo de Lenguaje Grande (LLM) (si la API Key de OpenAI está configurada) para la Comprensión del Lenguaje Natural (NLU), permitiendo detectar la intención del usuario (ej: saludo, buscar producto, despedida) a partir de su entrada de texto.
-   Si la intención es "buscar producto" y se extrae una consulta:
    -   Decide llamar a la herramienta `catalog_search_tool`.
    -   El grafo ejecuta la herramienta.
    -   En el siguiente turno, el `ConversationalMasterAgent` procesa los resultados de la búsqueda y los presenta al usuario.
-   Si el LLM no está configurado, recurre a una lógica de fallback simple (eco de mensajes, manejo de "adiós", y una forma de _forzar_ la búsqueda con "busca [término]").

El `CatalogSearchAgent` ha sido refactorizado como una herramienta (`catalog_search_tool`) y está integrado en este flujo básico. Los otros agentes especializados (`WishlistAgent`, `ShoppingPlannerAgent`) aún no están integrados como herramientas en el flujo conversacional.

## Cómo Ejecutar

### Requisitos Previos
Asegúrate de tener Python 3.9 o superior instalado.

### Configuración del Entorno Virtual e Instalación de Dependencias

**Opción 1: Usando los scripts de configuración (Recomendado)**

Estos scripts automatizan la creación del entorno virtual y la instalación de dependencias.

*   **Para MacOS y Linux:**
    Abre una terminal en la raíz del proyecto y ejecuta:
    ```bash
    source setup.sh
    ```
    Este script creará el entorno virtual `.venv` si no existe, lo activará e instalará las dependencias listadas en `requirements.txt`.

*   **Para Windows:**
    Abre una terminal (CMD o PowerShell) en la raíz del proyecto y ejecuta:
    ```bash
    setup.bat
    ```
    Este script instalará las dependencias de `requirements.txt` y también instalará el proyecto en modo editable (usando `setup.py`). Asume que tienes un entorno virtual ya creado y activado, o que deseas instalarlo globalmente (no recomendado para desarrollo). Para una gestión de entorno virtual más explícita en Windows antes de correr `setup.bat`:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    setup.bat
    ```
    *(Nota: `python` podría ser `python3` dependiendo de tu instalación).*


**Opción 2: Configuración Manual**

Si prefieres configurar el entorno manualmente:

1.  **Crea un entorno virtual:**
    Desde la raíz del proyecto:
    ```bash
    python -m venv .venv
    ```
    *(Usa `python3` si es necesario en tu sistema).*

2.  **Activa el entorno virtual:**
    *   MacOS y Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   Windows (CMD):
        ```bash
        .venv\Scripts\activate.bat
        ```
    *   Windows (PowerShell):
        ```bash
        .venv\Scripts\Activate.ps1
        ```
        *(Si la ejecución de scripts está deshabilitada en PowerShell, puede que necesites ejecutar `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` primero).*

3.  **Instala las dependencias:**
    Una vez activado el entorno virtual, instala las dependencias desde `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    Opcionalmente, si quieres instalar el proyecto de forma editable (útil para desarrollo del propio paquete):
    ```bash
    pip install -e .
    ```
    Las dependencias principales incluyen `langgraph`, `langchain`, `langchain_core`, `langchain-openai`, `python-dotenv`, y `pydantic`.

    Para la visualización del grafo (opcional, y puede requerir Graphviz instalado en el sistema):
    ```bash
    # pip install pygraphviz
    ```

### Configuración de la API Key de OpenAI
**Este paso es crucial para que funcionen las características de Inteligencia Artificial.**

1.  **Copia el archivo de ejemplo**: En la raíz del proyecto, encontrarás un archivo llamado `.env.example`. Copia este archivo y renombra la copia a `.env`.
2.  **Edita el archivo `.env`**: Abre el archivo `.env` con un editor de texto.
3.  **Añade tu API Key**: Modifica la línea `OPENAI_API_KEY="sk-tu_api_key_aqui"` reemplazando `"sk-tu_api_key_aqui"` con tu API Key real de OpenAI.
4.  **Modelo (Opcional)**: Puedes especificar el modelo de OpenAI en la línea `OPENAI_MODEL_NAME="gpt-4o-mini"`. Si esta línea no existe o está comentada, el sistema usará "gpt-4o-mini" por defecto para las nuevas funcionalidades de IA.

El archivo `.env` está incluido en `.gitignore`, por lo que tu API key no se compartirá si subes el código a un repositorio Git.

Si no configuras la API Key, el programa se ejecutará, pero las funcionalidades que dependen de un LLM (como el análisis de wishlist o la generación de consejos por el `ConversationalMasterAgent` en el futuro) mostrarán un error indicando que la API Key no fue encontrada o es inválida. El esqueleto actual del chat funcionará, pero sin la inteligencia del LLM.

### Ejecutar el Agente Conversacional (Esqueleto)
El script principal `src/main.py` ahora inicia una interfaz de chat en la línea de comandos (CLI) para interactuar con el esqueleto del `ConversationalMasterAgent`.
Para ejecutarlo desde la raíz del repositorio:
```bash
python -m src.main
```
Se te presentará un prompt `👤 Tú: `. Puedes escribir mensajes y el agente (en su estado actual de esqueleto) responderá de forma simple. Escribe "adiós" o "salir" para terminar la sesión.

Los datos iniciales (catálogo de productos, ejemplos de wishlist de redes sociales, etc.) se cargan una vez al inicio para que estén disponibles en el estado del agente, en preparación para cuando el `ConversationalMasterAgent` pueda usar herramientas que accedan a estos datos.

### Ejecutar Pruebas Específicas de Componentes
Algunos módulos tienen bloques `if __name__ == '__main__':` que permiten probar su funcionalidad de forma aislada:
-   **Probar la herramienta de búsqueda en catálogo**:
    ```bash
    python src/agent/search_handler.py
    ```
-   **Probar el WishlistAgent (requiere API Key configurada para ver resultados IA)**:
    ```bash
    python src/agent/wishlist_agent.py
    ```
-   **Probar el esqueleto del MasterAgent**:
    ```bash
    python src/agent/master_agent.py
    ```

### Ejecutar las Pruebas Unitarias (Existentes)
Para ejecutar las pruebas unitarias, navega a la raíz del repositorio y ejecuta:
```bash
python -m unittest discover -s tests -v
```
Esto descubrirá y correrá todas las pruebas definidas en la carpeta `tests/`.

## Flujo de la Demostración (`src/main.py`)

## Flujo de la Demostración (Actual con Esqueleto Conversacional)

El script `src/main.py` ahora opera de la siguiente manera:

1.  **Inicialización**:
    *   Se crea el grafo conversacional (`create_conversational_graph`).
    *   Se inicializa el `AgentState` con campos para el historial de conversación, datos de productos (cargados una vez), perfil de usuario, etc.
    *   Se cargan los datos simulados (catálogo, Instagram, Pinterest, carritos) en el estado inicial. Esto se hace para que las futuras herramientas tengan acceso a estos datos sin necesidad de cargarlos en cada turno de conversación.
2.  **Bucle de Conversación (CLI)**:
    *   El programa entra en un bucle `while True`.
    *   **Entrada del Usuario**: Se solicita al usuario que ingrese un mensaje.
    *   **Actualización del Estado**: La entrada se almacena en `current_state['current_user_input']`.
    *   **Invocación del Grafo**: Se invoca el grafo conversacional.
        *   `get_input_node`: Recoge la entrada.
        *   `master_agent_node`: Ejecuta `run_conversational_master_agent`.
            *   **Si hay resultados de herramientas pendientes (ej: `catalog_search_output` del turno anterior)**: El `MasterAgent` los formatea en una respuesta para el usuario. `catalog_search_output` se limpia del estado.
            *   **Si NO hay resultados de herramientas**:
                *   El `MasterAgent` usa el LLM (si está configurado) para detectar la intención del `current_user_input`.
                *   Si la intención es "buscar\_producto" y se extrae una consulta, el `MasterAgent` decide llamar a `catalog_search_tool`. Su respuesta inmediata al usuario será algo como "Ok, buscando...".
                *   Para otras intenciones, formula una respuesta directa o decide terminar la conversación.
            *   El `current_user_input` se limpia del estado.
        *   **Enrutamiento Condicional (`route_after_master_agent`)**:
            *   Si se decidió llamar a una herramienta, el flujo va a `execute_tool_node`.
            *   Si no, va a `respond_to_user_node`.
        *   `execute_tool_node` (si se llamó):
            *   Ejecuta la herramienta especificada (ej: `catalog_search_tool`) con los argumentos proporcionados.
            *   Almacena el resultado en `state['catalog_search_output']`.
            *   El flujo vuelve al `master_agent_node` para procesar este resultado en el siguiente "sub-ciclo" del turno.
        *   `respond_to_user_node`: Prepara/registra la respuesta final del turno.
        *   **Condicional `should_loop_or_end`**: Si la acción es `end_conversation`, el grafo termina. Si no, vuelve a `get_input_node` para esperar la siguiente entrada del usuario.
    *   **Salida al Usuario**: La respuesta del agente (formulada por `master_agent_node` y almacenada en `master_agent_decision.response_text`) se muestra en la consola (actualmente los `print` están distribuidos en los nodos, pero el mensaje final al usuario es el de `master_agent_decision.response_text`).
    *   **Terminación**: Si el `master_agent_node` decide `end_conversation`, el bucle en `main.py` termina.

**Nota sobre el Flujo Anterior (Pipeline):**
La función `create_pipeline_graph()` en `src/agent/graph.py` contiene el grafo del pipeline anterior que procesaba los datos de forma lineal. Ya no es el flujo principal ejecutado por `main.py` pero se conserva como referencia o para posibles usos futuros.

## Próximos Pasos (Plan General)

Consultar el plan activo del agente IA para los detalles. La evolución se centrará en:
-   Dotar de inteligencia al `ConversationalMasterAgent` usando un LLM para interpretar la intención del usuario y enrutar a herramientas.
-   Refactorizar completamente los agentes especializados (`WishlistAgent`, `ShoppingPlannerAgent`, etc.) como herramientas LangChain.
-   Integrar estas herramientas para que el `ConversationalMasterAgent` las pueda invocar dinámicamente.
-   Mejorar el manejo del estado y el historial de la conversación.
-   Expandir las capacidades de cada agente especializado.
-   Mejorar el algoritmo de matching de productos (ej. usando embeddings o técnicas de NLP más avanzadas).
-   Refinar la lógica de priorización del plan de compra.
-   Implementar una interfaz de usuario (CLI o web básica) en lugar de simular la interacción en `main.py`.
-   Conectar con APIs reales de redes sociales y marketplaces (considerando políticas de acceso y privacidad).
-   Añadir persistencia para el estado del agente o los perfiles de usuario.
-   Optimizar el flujo del grafo para evitar la re-ejecución innecesaria de nodos.

### Expansión de la Visión y Aplicaciones Futuras
Además de las mejoras incrementales, se contempla expandir las capacidades del agente para incluir:
-   **Estrategias de Fidelización de Clientes**: Implementar mecánicas para fomentar la lealtad del cliente, como sistemas de puntos, recompensas por compras recurrentes, o recomendaciones personalizadas basadas en el historial a largo plazo.
-   **Mecanismos Avanzados para Impulsar Compras**:
    -   **Bundling Dinámico**: Sugerir paquetes de productos complementarios basados en el análisis de la wishlist y el comportamiento de compra.
    -   **Ofertas Personalizadas y Tiempo Limitado**: Generar y presentar ofertas únicas para el usuario, posiblemente integradas con alertas.
    -   **Comparación Inteligente**: Ayudar al usuario a comparar productos similares dentro del catálogo o incluso entre diferentes fuentes (si se expande el alcance).
-   **Programas de Monedero Digital (Wallet Prepaga)**:
    -   **Sistema de Prepago con Beneficios de Lealtad**: Permitir a los usuarios cargar fondos en un monedero digital y obtener beneficios adicionales (descuentos, acceso temprano a ofertas, etc.) por usarlo.
    -   **Gestión de "Float" de Clientes**: Implementar un sistema donde los fondos prepagados por los clientes puedan ser gestionados eficientemente, incentivando su uso dentro del ecosistema del marketplace.
    -   **Integración con Promociones**: Facilitar el uso del saldo del monedero para promociones especiales o cashback.
