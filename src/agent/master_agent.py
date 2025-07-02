from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.utils.config import get_llm # Para usar el LLM

# --- Modelos Pydantic para la Salida del LLM de Intención ---
class IntentDetectionOutput(BaseModel):
    intent: str = Field(description="La intención detectada del usuario. Debe ser una de: 'saludo', 'despedida', 'buscar_producto', 'crear_plan', 'pregunta_general', 'desconocido'.")
    extracted_query: Optional[str] = Field(description="Si la intención es 'buscar_producto', el término de búsqueda o producto que el usuario mencionó. Sino, null.", default=None)
    # Podríamos añadir más campos extraídos si es necesario, ej: presupuesto para 'crear_plan'.

class MasterAgentDecision(BaseModel):
    next_action: str # ej: "respond_to_user", "call_tool_catalog_search", "end_conversation"
    response_text: Optional[str] = None
    tool_to_call: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None

def run_conversational_master_agent(
    user_input: str,
    conversation_history: List[Tuple[str, str]],
    # El estado completo se pasa para acceder a los outputs de las herramientas
    # y para permitir que el MasterAgent limpie esos outputs después de procesarlos.
    # Sin embargo, para mantener la firma de la función más limpia para el LLM de intención,
    # podríamos pasar solo los campos necesarios o hacer que el nodo del grafo maneje la limpieza.
    # Por ahora, vamos a asumir que el nodo del grafo (`master_agent_node` en graph.py)
    # pasará `catalog_search_output` si existe y se encargará de limpiarlo del estado global.
    # Para este paso, modificaremos `master_agent_node` en `graph.py` para que pase
    # `catalog_search_output` a `run_conversational_master_agent` y luego lo limpie.
    # Así, `run_conversational_master_agent` solo necesita un nuevo parámetro.
    #
    # REVISIÓN: Es más limpio que run_conversational_master_agent reciba el estado completo (o al menos
    # los campos de output de herramientas) y sea responsable de indicar que se han procesado,
    # o que el nodo wrapper en graph.py lo haga.
    # Para este paso, hagamos que `run_conversational_master_agent` reciba `catalog_search_output`
    # y formule la respuesta. El nodo `master_agent_node` en `graph.py` limpiará el output del estado.

    # Nuevo parámetro para los resultados de la búsqueda
    catalog_search_results: Optional[List[Dict[str, Any]]] = None
) -> MasterAgentDecision:
    """
    Procesa la entrada del usuario, el historial de conversación y los resultados de herramientas
    (como catalog_search_results) para decidir la siguiente acción del agente conversacional.

    Puede detectar intenciones del usuario (usando LLM si está configurado), decidir llamar
    a herramientas, o formular respuestas directas. Si se proporcionan resultados de una
    herramienta, los procesa para informar al usuario.
    """
    print(f"--- CONVERSATIONAL MASTER AGENT ---")
    # print(f"Entrada del Usuario: {user_input}") # Se imprimirá si se procesa
    # print(f"Historial: {conversation_history}")
    # print(f"Resultados Búsqueda Catálogo: {catalog_search_results}")


    # --- Fase 1: Procesar resultados de herramientas (si los hay) ---
    if catalog_search_results is not None:
        print("--- MasterAgent: Procesando resultados de catalog_search_tool ---")
        if not catalog_search_results: # Lista vacía
            response_text = "No encontré productos que coincidan con tu búsqueda en el catálogo."
        elif isinstance(catalog_search_results, list) and len(catalog_search_results) > 0 and "error" in catalog_search_results[0]:
            response_text = f"Hubo un error al buscar en el catálogo: {catalog_search_results[0]['error']}"
        else:
            response_text = f"Encontré {len(catalog_search_results)} producto(s) para ti:\n"
            for i, prod in enumerate(catalog_search_results[:3]): # Mostrar hasta 3 productos
                response_text += f"{i+1}. {prod.get('name', 'N/A')} (Precio: {prod.get('price', 'N/A')} {prod.get('currency', '')})\n"
            if len(catalog_search_results) > 3:
                response_text += f"...y {len(catalog_search_results) - 3} más."

        # Después de procesar el resultado de la herramienta, la acción es responder y luego esperar nuevo input.
        return MasterAgentDecision(
            next_action="respond_to_user", # Esta acción luego llevará a get_input en el grafo
            response_text=response_text
        )

    # --- Fase 2: Procesar nueva entrada del usuario (si no hubo resultados de herramienta) ---
    print(f"Entrada del Usuario a procesar: {user_input}")

    # DEBUG: Forzar llamada a herramienta para prueba sin LLM de intención
    if user_input.lower().startswith("busca "):
        query = user_input[len("busca "):].strip()
        if query:
            print(f"DEBUG: Forzando llamada a catalog_search_tool con query: {query}")
            return MasterAgentDecision(
                next_action="call_tool",
                tool_to_call="catalog_search_tool",
                tool_input={"query": query},
                response_text=f"Ok, voy a buscar '{query}' en el catálogo..."
            )
    # FIN DEBUG

    if not user_input.strip() and not conversation_history:
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text="¡Hola! Soy tu asistente de compras personal. ¿Cómo puedo ayudarte hoy? Puedes pedirme que busque productos, por ejemplo."
        )
    elif not user_input.strip():
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text="Parece que no has dicho nada. ¿Hay algo en lo que pueda ayudarte?"
        )

    try:
        # Usar una temperatura baja para clasificación de intención, para que sea más determinista.
        # El nombre del modelo se toma de la configuración (get_llm maneja el default a gpt-4o-mini).
        llm = get_llm(temperature=0.0)
    except ValueError as e:
        # Fallback a lógica simple si el LLM no está disponible (ej: API key no configurada)
        print(f"ADVERTENCIA: Error al inicializar LLM en MasterAgent: {e}. Usando lógica de fallback.")
        if user_input.lower() in ["adiós", "salir", "exit", "quit", "bye"]:
            return MasterAgentDecision(next_action="end_conversation", response_text="¡Hasta luego!")
        return MasterAgentDecision(
            next_action="respond_to_user",
            response_text=f"Hubo un problema con mi cerebro IA (o no está configurado). Respuesta simple: Entendido, dijiste '{user_input}'."
        )

    # Formatear historial para el prompt del LLM
    N_history_turns = 3 # Considerar los últimos N turnos del historial
    # Cada turno en `conversation_history` es una tupla (speaker, text).
    # Necesitamos convertirlo a un string legible para el LLM.
    recent_history_tuples = conversation_history[-(N_history_turns*2):]
    formatted_history_str = "\n".join([f"{speaker}: {text}" for speaker, text in recent_history_tuples])

    intent_prompt_template = ChatPromptTemplate.from_template(INTENT_DETECTION_PROMPT_TEMPLATE)
    # Usar with_structured_output para obtener un objeto Pydantic directamente.
    intent_chain = intent_prompt_template | llm.with_structured_output(IntentDetectionOutput)

    response_text = ""
    next_action_str = "respond_to_user" # Default
    tool_to_call_str = None
    tool_input_dict = None

    try:
        print("--- MasterAgent: Detectando intención con LLM ---")
        intent_result = intent_chain.invoke({
            "user_input": user_input,
            "formatted_history": formatted_history_str,
            "N_history_turns": N_history_turns # Pasar N al prompt por si lo usa
        })
        print(f"Intención detectada por LLM: {intent_result.intent}, Query extraída: '{intent_result.extracted_query}'")

        detected_intent = intent_result.intent

        if detected_intent == "despedida":
            response_text = "¡Hasta luego! Ha sido un placer ayudarte con tus compras."
            next_action_str = "end_conversation"
        elif detected_intent == "saludo":
            response_text = "¡Hola! ¿En qué te puedo ayudar hoy con tus compras? Puedes pedirme que busque productos, por ejemplo."
        elif detected_intent == "buscar_producto":
            if intent_result.extracted_query:
                response_text = f"Ok, voy a buscar '{intent_result.extracted_query}' en el catálogo..."
                next_action_str = "call_tool" # Acción genérica para llamar herramientas
                tool_to_call_str = "catalog_search_tool"
                # El input para la herramienta se construye aquí.
                # 'marketplace_products' se tomará del estado global en el nodo ejecutor de herramientas.
                tool_input_dict = {"query": intent_result.extracted_query}
            else:
                response_text = "Parece que quieres buscar un producto, pero no entendí bien qué. ¿Podrías ser más específico?"
        elif detected_intent == "crear_plan":
            response_text = "¡Genial! Quieres un plan de compra. Esta función estará disponible en futuras versiones."
        elif detected_intent == "pregunta_general":
            response_text = "Esa es una buena pregunta. Actualmente estoy aprendiendo a buscar productos y pronto podré ayudarte con más cosas. ¿Qué te gustaría hacer?"
        else: # "desconocido" o no manejado explícitamente
            response_text = f"No estoy seguro de cómo ayudarte con '{user_input}'. ¿Podrías reformularlo o probar otra cosa, como pedirme que busque un producto?"

    except Exception as e_intent:
        print(f"Error durante la detección de intención con LLM: {e_intent}")
        # Fallback si el LLM falla después de ser inicializado
        response_text = f"Tuve algunos problemas para procesar tu solicitud con IA. Dijiste: '{user_input}'. ¿Podrías intentarlo de otra manera?"

    return MasterAgentDecision(
        next_action=next_action_str,
        response_text=response_text,
        tool_to_call=tool_to_call_str,
        tool_input=tool_input_dict
    )

INTENT_DETECTION_PROMPT_TEMPLATE = """
Eres el cerebro de un asistente de compras conversacional. Tu tarea es analizar la última entrada del usuario y el historial reciente de la conversación para determinar la intención principal del usuario.

Historial de Conversación Reciente (últimos {N_history_turns} turnos):
{formatted_history}

Última Entrada del Usuario:
"{user_input}"

Posibles Intenciones:
- "saludo": El usuario está iniciando la conversación o saludando.
- "despedida": El usuario quiere terminar la conversación (ej: "adiós", "salir").
- "buscar_producto": El usuario quiere encontrar uno o más productos. Intenta extraer el término de búsqueda o el tipo de producto.
- "crear_plan": El usuario quiere crear o modificar un plan de compra (ej: "hazme un plan", "añade esto a mi plan").
- "pregunta_general": El usuario está haciendo una pregunta general sobre el asistente, productos, etc., que no encaja en otras categorías.
- "desconocido": La intención del usuario no está clara o no se puede determinar con las opciones anteriores.

Considera el contexto del historial. Si el usuario dice "sí" después de que le ofreciste buscar algo, la intención es probablemente "buscar_producto" o una confirmación relacionada.

Responde ÚNICAMENTE con un objeto JSON que se ajuste al esquema de `IntentDetectionOutput`.
El objeto JSON debe tener las siguientes claves:
- "intent": (str) Una de las intenciones listadas arriba.
- "extracted_query": (Optional[str]) Si la intención es "buscar_producto", el término de búsqueda o producto que el usuario mencionó. Sino, null.

Ejemplos:
Usuario: "Hola" -> {{"intent": "saludo", "extracted_query": null}}
Usuario: "Quiero unos audifonos rojos" -> {{"intent": "buscar_producto", "extracted_query": "audifonos rojos"}}
Usuario: "busco una cafetera espresso" -> {{"intent": "buscar_producto", "extracted_query": "cafetera espresso"}}
Usuario: "adiós" -> {{"intent": "despedida", "extracted_query": null}}
Usuario: "Qué puedes hacer?" -> {{"intent": "pregunta_general", "extracted_query": null}}
Usuario: "Gracias, eso es todo" -> {{"intent": "despedida", "extracted_query": null}}
"""

if __name__ == '__main__':
    # Prueba simple
    history = [("user", "Hola"), ("ai", "Hola! ¿En qué puedo ayudarte?")]

    user_message = "Quiero buscar una cafetera"
    decision = run_conversational_master_agent(user_message, history)
    print(f"Decisión del Master Agent: {decision.model_dump_json(indent=2)}")

    user_message_exit = "adiós"
    decision_exit = run_conversational_master_agent(user_message_exit, history)
    print(f"Decisión del Master Agent (Exit): {decision_exit.model_dump_json(indent=2)}")
