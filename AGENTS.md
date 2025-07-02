# Directrices para el Agente IA (Jules)

Este documento contiene directrices y convenciones para el desarrollo de este proyecto por parte del agente IA.

## Estructura del Proyecto

-   Sigue la estructura de carpetas definida en el `README.md`.
-   Los datos simulados se almacenarán en la carpeta `data/` en formato JSON o CSV.
-   El código fuente principal residirá en la carpeta `src/`.
-   Las pruebas irán en la carpeta `tests/`.

## Convenciones de Código

-   Utiliza Python 3.9 o superior.
-   Sigue las convenciones de estilo de PEP 8.
-   Añade docstrings a todas las funciones y clases públicas.
-   Utiliza type hints para mejorar la legibilidad y mantenibilidad del código.
-   Escribe comentarios claros cuando la lógica no sea evidente.

## Desarrollo con LangGraph

-   La lógica principal del agente se implementará utilizando LangGraph.
-   Define nodos claros y cohesivos para cada paso del proceso.
-   Asegúrate de que el flujo del grafo sea lógico y fácil de seguir.

## Manejo de Datos

-   Para esta fase inicial, trabajaremos con datos simulados.
-   Define esquemas claros para los datos de entrada (guardados de Instagram, tableros de Pinterest, carritos abandonados) y los datos de productos del retailer.
-   Más adelante, se explorará la integración con APIs reales.

## Pruebas

-   Escribe pruebas unitarias para las funciones y módulos críticos.
-   Intenta seguir un enfoque de Desarrollo Guiado por Pruebas (TDD) cuando sea práctico.
-   Asegúrate de que las pruebas cubran los casos de uso principales y los casos límite.

## Commits y Ramas

-   Utiliza nombres de rama descriptivos para nuevas funcionalidades o correcciones (ej: `feature/nombre-funcionalidad`, `fix/descripcion-bug`).
-   Escribe mensajes de commit claros y concisos, siguiendo la convención de Conventional Commits si es posible (ej: `feat: Implementa ingesta de datos de Instagram`).

## Comunicación

-   Si tienes dudas sobre los requisitos o necesitas aclaraciones, pregunta antes de proceder.
-   Actualiza el plan (`set_plan`) si es necesario realizar cambios significativos en el enfoque.
-   Informa sobre el progreso y los bloqueos de manera proactiva.

## Consideraciones Específicas del Proyecto

-   **Privacidad**: Aunque trabajemos con datos simulados inicialmente, ten en cuenta las implicaciones de privacidad para cuando se manejen datos reales. El diseño debe ser consciente de la protección de datos.
-   **Precisión del Algoritmo**: La calidad de las recomendaciones es crucial. Desde el inicio, piensa en cómo se podría medir y mejorar la precisión.
-   **Dependencia de Terceros**: Sé consciente de los riesgos asociados a la dependencia de APIs externas (aunque no las usemos directamente en la fase de simulación).

Estas directrices podrán ser actualizadas a medida que el proyecto evolucione.
