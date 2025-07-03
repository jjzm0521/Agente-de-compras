from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.utils.config import get_llm

# --- Modelos Pydantic para la Salida Estructurada del LLM ---

class IntentDetectionOutput(BaseModel):
    """
    Define la estructura esperada de la salida del LLM para la detección de intenciones.
    Utilizado por `run_conversational_master_agent` para interpretar la respuesta del LLM.
    """
    intent: str = Field(
        description="La intención detectada del usuario. Debe ser una de: 'saludo', 'despedida', 'buscar_producto', 'crear_plan', 'pregunta_general', 'desconocido'."
    )
    extracted_query: Optional[str] = Field(
        default=None,
        description="Si la intención es 'buscar_producto', el término de búsqueda o producto que el usuario mencionó. Sino, null."
    )
    # Se podrían añadir más campos extraídos si fuera necesario para otras intenciones,
    # por ejemplo, un presupuesto si la intención fuera 'crear_plan_con_presupuesto'.

class MasterAgentDecision(BaseModel):
    """
    Representa la decisión tomada por el `run_conversational_master_agent`.
    Indica la próxima acción a realizar en el grafo del agente.
    """
    next_action: str = Field(
        description="La próxima acción que el grafo debe tomar. Ej: 'respond_to_user', 'call_tool', 'end_conversation'."
    )
    response_text: Optional[str] = Field(
        default=None,
        description="El texto de la respuesta que el agente debe dar al usuario (si la acción es 'respond_to_user' o si se acompaña una llamada a herramienta)."
    )
    tool_to_call: Optional[str] = Field(
        default=None,
        description="El nombre de la herramienta a llamar si `next_action` es 'call_tool'. Ej: 'catalog_search_tool'."
    )
    tool_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="El diccionario de entrada para la herramienta a llamar."
    )

# --- Lógica Principal del Master Agent ---

def run_conversational_master_agent(
    user_input: str,
    conversation_history: List[Tuple[str, str]],
    catalog_search_results: Optional[List[Dict[str, Any]]] = None
) -> MasterAgentDecision:
    """
    Procesa la entrada del usuario, el historial de conversación y los resultados de herramientas
    (como `catalog_search_results`) para decidir la siguiente acción del agente conversacional.

    Este agente opera en dos fases principales:
    1.  Si hay resultados de una herramienta (ej: `catalog_search_results`), los procesa y
        formula una respuesta para el usuario.
    2.  Si no hay resultados de herramientas pendientes, procesa la nueva `user_input`:
        a.  Intenta detectar la intención del usuario utilizando un LLM (si está configurado).
        b.  Basado en la intención, decide si responder directamente, llamar a una herramienta
            (ej: `catalog_search_tool`), o finalizar la conversación.
        c.  Si el LLM no está disponible o falla, recurre a una lógica de fallback simple.

    Args:
        user_input: La última entrada de texto del usuario.
        conversation_history: Una lista de tuplas (hablante, texto) que representa el historial
                              de la conversación. El hablante puede ser "user" o "ai".
        catalog_search_results: Resultados opcionales de la herramienta de búsqueda en catálogo,
                                 provenientes de una ejecución anterior en el grafo. Puede ser
                                 una lista de productos o un diccionario de error.

    Returns:
        Un objeto `MasterAgentDecision` que contiene la acción a seguir, el texto de respuesta
        (si aplica), y detalles de la herramienta a llamar (si aplica).
    """
    print(f"--- CONVERSATIONAL MASTER AGENT ---")
    # Descomentar para debugging detallado:
    # print(f"  Input del Usuario: '{user_input}'")
    # print(f"  Historial (últimos {len(conversation_history)} turnos): {conversation_history}")
    # if catalog_search_results:
    #     print(f"  Resultados Búsqueda Catálogo: {len(catalog_search_results)} items")

    # --- Fase 1: Procesar resultados de herramientas pendientes (si los hay) ---
    if catalog_search_results is not None:
        print("--- MasterAgent: Procesando resultados de catalog_search_tool ---")
        if not catalog_search_results:  # Lista vacía indica que no se encontraron productos
            response_text = "No encontré productos que coincidan con tu búsqueda en el catálogo."
        # Comprobar si el primer item de resultados es un diccionario de error
        elif isinstance(catalog_search_results, list) and \
             len(catalog_search_results) > 0 and \
             isinstance(catalog_search_results[0], dict) and \
             "error" in catalog_search_results[0]: # Asumiendo que la herramienta devuelve [{"error": "mensaje"}]
            response_text = f"Hubo un error al buscar en el catálogo: {catalog_search_results[0]['error']}"
        else:
            # Formatear una respuesta con los productos encontrados
            response_text = f"Encontré {len(catalog_search_results)} producto(s) para ti:\n"
            for i, prod in enumerate(catalog_search_results[:3]):  # Mostrar hasta 3 productos para brevedad
                response_text += f"{i+1}. {prod.get('name', 'Nombre no disponible')} " \
                                 f"(Precio: {prod.get('price', 'N/A')} {prod.get('currency', '')})\n"
            if len(catalog_search_results) > 3:
                response_text += f"...y {len(catalog_search_results) - 3} más."

        # Después de procesar el resultado de la herramienta, la acción es responder al usuario.
        # El grafo luego esperará una nueva entrada del usuario.
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text=response_text
        )

    # --- Fase 2: Procesar nueva entrada del usuario (si no hubo resultados de herramienta) ---
    print(f"--- MasterAgent: Procesando nueva entrada del usuario: '{user_input}' ---")

    # Lógica de saludo inicial o si el usuario no ingresa texto
    if not user_input.strip() and not conversation_history: # Primer turno, sin input
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text="¡Hola! Soy tu asistente de compras personal. ¿Cómo puedo ayudarte hoy? Puedes pedirme que busque productos, por ejemplo."
        )
    elif not user_input.strip(): # Input vacío en un turno posterior
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text="Parece que no has dicho nada. ¿Hay algo en lo que pueda ayudarte?"
        )

    # DEBUG: Bloque para forzar llamada a herramienta (útil si el LLM de intención no funciona o para pruebas rápidas)
    # Si el usuario escribe "busca [algo]", se salta la detección de intención y llama directamente a la herramienta.
    if user_input.lower().startswith("busca "):
        query = user_input[len("busca "):].strip()
        if query:
            print(f"DEBUG: Forzando llamada a catalog_search_tool con query: '{query}'")
            return MasterAgentDecision(
                next_action="call_tool",
                tool_to_call="catalog_search_tool",
                tool_input={"query": query}, # marketplace_products se inyectará desde el estado del grafo
                response_text=f"Ok, voy a buscar '{query}' en el catálogo..."
            )
    # FIN DEBUG

    # Intentar inicializar el LLM para la detección de intención.
    # Se usa una temperatura baja para que la clasificación de intención sea más determinista.
    try:
        llm = get_llm(temperature=0.0) # get_llm maneja el modelo por defecto (ej: gpt-4o-mini)
    except ValueError as e:
        # Fallback a lógica simple si el LLM no está disponible (ej: API key no configurada)
        print(f"ADVERTENCIA: Error al inicializar LLM en MasterAgent: {e}. Usando lógica de fallback simple.")
        if user_input.lower().strip() in ["adiós", "salir", "exit", "quit", "bye", "chao"]:
            return MasterAgentDecision(next_action="end_conversation", response_text="¡Hasta luego! Que tengas un buen día.")
        # Respuesta genérica si el LLM no funciona
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text=f"Mis circuitos de IA están un poco revueltos ahora mismo (o no están configurados). Entendí que dijiste: '{user_input}'. Prueba con algo simple como 'busca [producto]'."
        )

    # Formatear el historial de conversación para el prompt del LLM
    # Considerar los últimos N turnos para dar contexto al LLM.
    N_history_turns = 3
    # El historial en `conversation_history` es [(speaker, text), (speaker, text), ...]
    # Tomamos los últimos N*2 items porque cada turno tiene entrada de usuario y respuesta de IA.
    recent_history_tuples = conversation_history[-(N_history_turns*2):]
    formatted_history_str = "\n".join([f"{speaker.capitalize()}: {text}" for speaker, text in recent_history_tuples])

    # Crear la cadena (chain) de Langchain para la detección de intención.
    # Se usa `with_structured_output` para obtener un objeto Pydantic `IntentDetectionOutput` directamente.
    intent_prompt_template = ChatPromptTemplate.from_template(INTENT_DETECTION_PROMPT_TEMPLATE)
    intent_chain = intent_prompt_template | llm.with_structured_output(IntentDetectionOutput)

    # Variables para almacenar la decisión final
    response_text = ""
    next_action_str = "respond_to_user"  # Acción por defecto si nada más se decide
    tool_to_call_str = None
    tool_input_dict = None

    try:
        print("--- MasterAgent: Detectando intención con LLM ---")
        # Invocar la cadena de detección de intención
        intent_result: IntentDetectionOutput = intent_chain.invoke({
            "user_input": user_input,
            "formatted_history": formatted_history_str,
            "N_history_turns": N_history_turns
        })
        print(f"Intención detectada por LLM: '{intent_result.intent}', Query extraída: '{intent_result.extracted_query}'")

        detected_intent = intent_result.intent

        # Lógica basada en la intención detectada
        if detected_intent == "despedida":
            response_text = "¡Hasta luego! Ha sido un placer ayudarte con tus compras."
            next_action_str = "end_conversation"
        elif detected_intent == "saludo":
            response_text = "¡Hola de nuevo! ¿En qué más puedo ayudarte hoy?"
            if not conversation_history: # Si es el primer saludo real
                 response_text = "¡Hola! Soy tu asistente de compras. ¿Buscas algo en especial?"
        elif detected_intent == "buscar_producto":
            if intent_result.extracted_query:
                response_text = f"Entendido. Voy a buscar '{intent_result.extracted_query}' en nuestro catálogo..."
                next_action_str = "call_tool" # Indica al grafo que debe llamar una herramienta
                tool_to_call_str = "catalog_search_tool" # Nombre de la herramienta a invocar
                # El input para la herramienta. 'marketplace_products' se inyectará
                # desde el estado del grafo por el nodo que ejecuta la herramienta.
                tool_input_dict = {"query": intent_result.extracted_query}
            else:
                # El LLM indicó buscar producto pero no pudo extraer la query
                response_text = "Parece que quieres buscar un producto, pero no entendí bien qué producto. ¿Podrías ser más específico, por favor?"
        elif detected_intent == "crear_plan":
            # Funcionalidad futura, responder informativamente.
            response_text = "¡Genial! Quieres un plan de compra. Esta función es muy interesante y estará disponible en futuras versiones de mi sistema."
        elif detected_intent == "pregunta_general":
            response_text = "Esa es una buena pregunta. Actualmente, mi especialidad es ayudarte a buscar productos en nuestro catálogo. Pronto aprenderé a hacer más cosas. ¿Te gustaría buscar algún producto?"
        else:  # Caso "desconocido" o intenciones no manejadas explícitamente
            response_text = f"No estoy completamente seguro de cómo ayudarte con eso ('{user_input}'). ¿Podrías intentar reformular tu solicitud? Por ejemplo, puedes pedirme que 'busque [nombre del producto]'."

    except Exception as e_intent:
        print(f"Error durante la detección de intención con LLM o en la lógica posterior: {e_intent}")
        # Fallback si el LLM falla después de ser inicializado o hay otro error en esta fase.
        response_text = f"Tuve algunos problemas para procesar tu solicitud ('{user_input}') con mi inteligencia artificial. ¿Podrías intentarlo de otra manera o ser un poco más específico?"

    return MasterAgentDecision(
        next_action=next_action_str,
        response_text=response_text,
        tool_to_call=tool_to_call_str,
        tool_input=tool_input_dict
    )

# --- Plantilla de Prompt para Detección de Intención ---
# Esta plantilla guía al LLM para que clasifique la entrada del usuario y extraiga información.
INTENT_DETECTION_PROMPT_TEMPLATE = """
Eres el cerebro de un asistente de compras conversacional avanzado. Tu tarea principal es analizar la última entrada del usuario y el historial reciente de la conversación para determinar la intención principal del usuario y extraer información relevante si es necesario.

Considera el contexto del historial de conversación. Por ejemplo, si el usuario dice "sí" después de que le ofreciste buscar algo, la intención es probablemente una confirmación relacionada con la búsqueda.

Historial de Conversación Reciente (los últimos {N_history_turns} turnos de diálogo):
{formatted_history}

Última Entrada del Usuario:
"{user_input}"

---
Instrucciones para la Clasificación de Intención:
Debes clasificar la "Última Entrada del Usuario" en UNA de las siguientes intenciones:

1.  `saludo`: El usuario está iniciando la conversación, saludando o respondiendo a un saludo.
    Ejemplos: "Hola", "Buenas tardes", "Qué tal?"
2.  `despedida`: El usuario quiere terminar la conversación.
    Ejemplos: "Adiós", "Hasta luego", "Eso es todo, gracias", "chao", "salir".
3.  `buscar_producto`: El usuario quiere encontrar uno o más productos. Si esta es la intención, DEBES extraer el término de búsqueda o el tipo de producto en el campo `extracted_query`.
    Ejemplos: "Busco una laptop", "Tienes camisetas rojas?", "Quiero ver precios de cafeteras", "Necesito audífonos inalámbricos".
4.  `crear_plan`: El usuario expresa deseo de crear, modificar o consultar un plan de compra o una lista de deseos. (Actualmente una funcionalidad futura).
    Ejemplos: "Hazme un plan de compra", "Añade esto a mi wishlist", "Qué tengo en mi plan?".
5.  `pregunta_general`: El usuario está haciendo una pregunta general sobre el asistente, sus capacidades, el proceso de compra, o cualquier otra cosa que no encaje directamente en las categorías anteriores y no sea una búsqueda de producto.
    Ejemplos: "¿Qué puedes hacer?", "¿Cómo funciona esto?", "¿Hay ofertas hoy?".
6.  `desconocido`: La intención del usuario no está clara, es ambigua, o no se puede determinar con certeza a partir de las opciones anteriores. También usa esto para comentarios irrelevantes o demasiado complejos para las capacidades actuales.
    Ejemplos: "El cielo es azul", "asdfghjkl", "Cuéntame un chiste sobre compras".

---
Formato de Salida Obligatorio:
Responde ÚNICAMENTE con un objeto JSON que se ajuste al esquema de `IntentDetectionOutput`. No incluyas NINGÚN texto adicional antes o después del objeto JSON.
El objeto JSON debe tener EXACTAMENTE las siguientes claves:
-   `intent`: (str) Una de las intenciones listadas arriba (ej: "buscar_producto").
-   `extracted_query`: (Optional[str]) Si la intención es "buscar_producto", este DEBE ser el término de búsqueda o producto que el usuario mencionó (ej: "laptop gamer", "camisetas rojas"). Si la intención NO es "buscar_producto", este campo DEBE ser `null`.

Ejemplos de Salida JSON esperada:
Usuario: "Hola" -> {{"intent": "saludo", "extracted_query": null}}
Usuario: "Quiero unos audifonos rojos" -> {{"intent": "buscar_producto", "extracted_query": "audifonos rojos"}}
Usuario: "busco una cafetera espresso" -> {{"intent": "buscar_producto", "extracted_query": "cafetera espresso"}}
Usuario: "adiós" -> {{"intent": "despedida", "extracted_query": null}}
Usuario: "Qué puedes hacer?" -> {{"intent": "pregunta_general", "extracted_query": null}}
Usuario: "Gracias, eso es todo" -> {{"intent": "despedida", "extracted_query": null}}
Usuario: "Y si compro dos?" -> {{"intent": "desconocido", "extracted_query": null}} (Asumiendo que no hay contexto previo claro)
"""

# --- Bloque de Prueba (ejecutar con `python src/agent/master_agent.py`) ---
if __name__ == '__main__':
    # Simulación de una conversación para probar el agente
    print("--- INICIANDO PRUEBA DEL MASTER AGENT ---")

    # Configurar el historial de conversación (simulado)
    # Nota: Para que el LLM funcione, se necesita una API Key de OpenAI válida en .env
    # y las dependencias de Langchain instaladas.
    example_history = [
        ("user", "Hola, buenos días"),
        ("ai", "¡Hola! Buenos días. Soy tu asistente de compras. ¿En qué puedo ayudarte hoy?")
    ]

    # Caso 1: Usuario quiere buscar un producto
    user_message_search = "Estoy buscando unos audífonos inalámbricos con cancelación de ruido"
    print(f"\n[Prueba 1] Usuario dice: '{user_message_search}'")
    decision_search = run_conversational_master_agent(
        user_input=user_message_search,
        conversation_history=example_history
    )
    print(f"Decisión del Master Agent: {decision_search.model_dump_json(indent=2)}")

    # Añadir al historial para la siguiente prueba
    if decision_search.response_text:
        example_history.append(("user", user_message_search))
        example_history.append(("ai", decision_search.response_text))

    # Caso 2: Usuario pregunta algo general después de una búsqueda simulada
    # (simulamos que la búsqueda anterior ocurrió y el agente está listo para más)
    user_message_general = "Y qué tipo de audífonos tienes en oferta?"
    print(f"\n[Prueba 2] Usuario dice: '{user_message_general}'")
    # Simulamos que la herramienta de búsqueda ya se ejecutó y devolvió resultados
    mock_search_results = [
        {"name": "Audífono SuperBass Pro", "price": 99.99, "currency": "USD"},
        {"name": "Audífono AirSound Light", "price": 59.99, "currency": "USD"}
    ]
    # Esta llamada simula que el agente está procesando los resultados de una herramienta
    decision_general_after_search = run_conversational_master_agent(
        user_input="Ok, muéstrame más detalles del SuperBass Pro", # Nueva entrada del usuario que podría seguir a la presentación de resultados
        conversation_history=example_history, # Historial hasta antes de mostrar los resultados
        catalog_search_results=mock_search_results # Pasamos resultados simulados de la herramienta
    )
    print(f"Decisión del Master Agent (procesando resultados de herramienta): {decision_general_after_search.model_dump_json(indent=2)}")

    # Actualizar historial con la respuesta del agente a los resultados de la herramienta
    if decision_general_after_search.response_text:
         # Asumimos que la entrada del usuario "Ok, muéstrame más detalles..." no se añade aquí,
         # ya que el agente respondió a los *resultados de la herramienta*, no a esa entrada directamente en esta pasada.
         # El flujo del grafo manejaría la nueva entrada "Ok, muéstrame..." en el siguiente ciclo.
         # Para simplificar la prueba, añadimos la respuesta del agente al historial.
         example_history.append(("ai", decision_general_after_search.response_text))

    # Ahora, el usuario hace la pregunta general sin resultados de herramienta pendientes.
    # El historial ahora incluye la respuesta del agente sobre los productos encontrados.
    print(f"\n[Prueba 2b] Usuario dice: '{user_message_general}' (después de que el agente presentó resultados)")
    decision_general_question = run_conversational_master_agent(
        user_input=user_message_general, # "Y qué tipo de audífonos tienes en oferta?"
        conversation_history=example_history # Historial actualizado
    )
    print(f"Decisión del Master Agent (pregunta general): {decision_general_question.model_dump_json(indent=2)}")
    if decision_general_question.response_text:
        example_history.append(("user", user_message_general))
        example_history.append(("ai", decision_general_question.response_text))


    # Caso 3: Usuario se despide
    user_message_exit = "Muchas gracias, eso es todo por ahora. Adiós."
    print(f"\n[Prueba 3] Usuario dice: '{user_message_exit}'")
    decision_exit = run_conversational_master_agent(
        user_input=user_message_exit,
        conversation_history=example_history
    )
    print(f"Decisión del Master Agent (Exit): {decision_exit.model_dump_json(indent=2)}")
    print("\n--- FIN DE PRUEBA DEL MASTER AGENT ---")
