from src.agent.graph import create_graph, AgentState

def run_agent_demo():
    """
    Ejecuta una demostración del agente de planificación de compras.
    """
    print("🚀 Iniciando Agente de Plan de Compra Personalizado 🚀")

    # Crear el grafo del agente
    app = create_graph()

    # Estado inicial para la ejecución
    # Podríamos pasar aquí información del usuario si la tuviéramos
    initial_state: AgentState = {
        "marketplace_products": None,
        "instagram_saves": None,
        "pinterest_boards": None,
        "abandoned_carts": None,
        "identified_user_wishlist": [],
        "user_profile": {"budget": 1000, "preferred_categories": ["Electrónica", "Hogar"]},
        "enriched_wishlist": [],
        "shopping_plan": {},
        "search_criteria": None,
        "search_results": [],
        "ia_categorized_wishlist": None,
        "wishlist_agent_error": None,
        "raw_cart_items": None,

        # Para el MasterAgent Conversacional
        "conversation_history": [],
        "current_user_input": None,
        "master_agent_decision": None
    }

    # Ahora `create_graph` se refiere a `create_conversational_graph`
    # El flujo de pipeline anterior (incluyendo la doble invocación) ya no se usa aquí.
    # Se implementará un bucle de conversación simple.

    print("🚀 Iniciando Agente de Compras Conversacional (Esqueleto) 🚀")
    print("Escribe 'adiós' o 'salir' para terminar.")

    # Crear el grafo conversacional
    # La función create_graph() en graph.py ahora devuelve el grafo conversacional.
    app = create_graph()

    # Estado inicial para la conversación
    current_state: AgentState = {
        "marketplace_products": None, # Se cargarán por herramientas si es necesario
        "instagram_saves": None,
        "pinterest_boards": None,
        "abandoned_carts": None,
        "identified_user_wishlist": [], # Legacy, podría eliminarse o usarse por herramientas
        "user_profile": {"budget": 1000, "preferred_categories": ["Electrónica", "Hogar"]},
        "enriched_wishlist": [],
        "shopping_plan": {},
        "search_criteria": None,
        "search_results": [],
        "ia_categorized_wishlist": None,
        "wishlist_agent_error": None,
        "raw_cart_items": None,
        "conversation_history": [],
        "current_user_input": None,
        "master_agent_decision": None,
        "catalog_search_output": None # Inicializar resultado de búsqueda
    }

    # Cargar datos una vez al inicio para que estén disponibles para las herramientas (simulación)
    # En un sistema más avanzado, las herramientas cargarían datos bajo demanda o el MasterAgent lo orquestaría.
    print("Cargando datos iniciales para el entorno del agente...")
    current_state['marketplace_products'] = data_loader.get_marketplace_products()
    current_state['instagram_saves'] = data_loader.get_instagram_saves()
    current_state['pinterest_boards'] = data_loader.get_pinterest_boards()
    current_state['abandoned_carts'] = data_loader.get_abandoned_carts()
    print("Datos iniciales cargados.")

    while True:
        try:
            user_input = input("👤 Tú: ")
            current_state["current_user_input"] = user_input

            # Invocar el grafo con el input del usuario
            # El recursion_limit puede necesitar ajuste para conversaciones más largas o complejas.
            updated_state = app.invoke(current_state, config={"recursion_limit": 20})
            current_state = updated_state # Actualizar el estado para el siguiente turno

            master_decision = current_state.get("master_agent_decision", {})

            # La respuesta al usuario ya se imprime dentro del nodo respond_to_user_node (simulado)
            # o aquí podríamos tomar master_decision.response_text para mostrarlo.
            # Por ahora, el nodo `respond_to_user_node` ya lo imprime.

            if master_decision.get("next_action") == "end_conversation":
                # El mensaje de despedida ya lo imprime el respond_to_user_node
                break

        except KeyboardInterrupt:
            print("\n👋 Saliendo del agente conversacional.")
            break
        except Exception as e:
            print(f"\n💥 Ocurrió un error inesperado: {e}")
            print("Reiniciando ciclo de conversación o terminando...")
            # Podríamos optar por resetear parte del estado o simplemente terminar.
            # Por ahora, terminaremos si hay un error no manejado.
            break

    print("\n✨ Sesión de Agente Conversacional Finalizada ✨")

if __name__ == "__main__":
    # Importar data_loader aquí porque se usa en el nuevo run_agent_demo
    from src.utils import data_loader
    run_agent_demo()
