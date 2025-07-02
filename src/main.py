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
        "search_criteria": None, # Inicializar search_criteria
        "search_results": []     # Inicializar search_results
    }

    print("\n--- 📊 Ejecutando Flujo del Agente (Plan de Compra Inicial) 📊 ---")
    # Invocar el grafo con el estado inicial
    # La configuración de 'recursion_limit' puede ser necesaria para grafos más complejos o largos.
    # Ejecutamos una primera vez para el plan de compra
    current_state = app.invoke(initial_state, config={"recursion_limit": 15})

    print("\n--- ✅ Flujo del Plan de Compra Completado ✅ ---")
    print("\n--- 📝 Resumen Intermedio del Estado del Agente (Post-Plan) 📝 ---")
    # Mostrar un breve resumen aquí puede ser útil para depurar o entender el estado antes de la búsqueda
    if current_state.get('shopping_plan'):
        plan = current_state['shopping_plan']
        print(f"🛍️ Plan de Compra: {len(plan.get('items_to_buy', []))} items para comprar. Costo: {plan.get('estimated_total_cost')} {plan.get('currency', '')}")

    # --- Simulación de Búsqueda de Productos ---
    print("\n--- 🔍 Iniciando Simulación de Búsqueda de Productos 🔍 ---")
    # Establecer criterios de búsqueda en el estado actual
    # Ejemplo 1: Buscar cafeteras baratas
    current_state['search_criteria'] = {"query": "cafetera", "max_price": 350.00, "in_stock": True}

    # Volver a invocar el grafo. Como el grafo ahora fluye hacia la búsqueda DESPUÉS del plan,
    # y el estado se mantiene, debería ejecutar el nodo de búsqueda.
    # NOTA: LangGraph generalmente reinicia desde el punto de entrada si no se manejan los puntos de continuación
    # de forma más explícita para flujos más complejos o interactivos.
    # Para este ejemplo secuencial extendido, la invocación completa funcionará,
    # aunque una implementación más robusta usaría `stream` o gestionaría puntos de continuación.
    # Dado que nuestro flujo es lineal (plan -> search -> END), una nueva invocación
    # con el estado actualizado que incluye 'search_criteria' debería funcionar,
    # pero es importante notar que RECORRERÁ TODO EL GRAFO DE NUEVO.
    # Una mejor aproximación para un agente interactivo sería tener un grafo que pueda
    # saltar a nodos específicos o un bucle de control externo.
    # Por simplicidad, aquí re-invocamos. Los nodos anteriores simplemente re-procesarán.

    # Para evitar que los nodos anteriores se ejecuten de nuevo innecesariamente si ya tienen datos,
    # podríamos hacerlos más idempotentes o usar un punto de entrada diferente para la búsqueda.
    # Por ahora, dejaremos que se re-ejecuten, ya que no tienen efectos secundarios dañinos aquí.
    # Una alternativa sería diseñar el grafo con puntos de entrada condicionales o usar `app.stream()`
    # para un control más fino sobre qué nodos ejecutar.

    print(f"\n--- 📊 Ejecutando Flujo del Agente (con Criterios de Búsqueda: {current_state['search_criteria']}) 📊 ---")
    # La segunda invocación procesará todo el grafo de nuevo, pero esta vez `search_criteria`
    # tendrá un valor, lo que permitirá que el nodo `search_products_node` realice la búsqueda.
    final_state = app.invoke(current_state, config={"recursion_limit": 15}) # Usar current_state

    print("\n--- ✅ Flujo de Búsqueda Completado ✅ ---")
    print("\n--- 📝 Resumen del Estado Final del Agente (Post-Búsqueda) 📝 ---")

    if final_state.get('marketplace_products'):
        print(f"🛒 Productos del Marketplace cargados: {len(final_state['marketplace_products'])} items")
    else:
        print("🛒 Productos del Marketplace: No cargados o error.")

    if final_state.get('instagram_saves') and final_state['instagram_saves'].get('saved_items'):
        print(f"📸 Saves de Instagram procesados: {len(final_state['instagram_saves']['saved_items'])} items")
    else:
        print("📸 Saves de Instagram: No cargados o sin items.")

    if final_state.get('pinterest_boards') and final_state['pinterest_boards'].get('boards'):
        num_pins = sum(len(b.get('pins', [])) for b in final_state['pinterest_boards']['boards'])
        print(f"📌 Pines de Pinterest procesados: {num_pins} pines en {len(final_state['pinterest_boards']['boards'])} tableros")
    else:
        print("📌 Pines de Pinterest: No cargados o sin tableros/pines.")

    if final_state.get('abandoned_carts'):
        print(f"💨 Carritos Abandonados procesados: {len(final_state['abandoned_carts'])} carritos")
    else:
        print("💨 Carritos Abandonados: No cargados o sin datos.")

    if final_state.get('identified_user_wishlist'):
        print(f"📋 Wishlist Identificada: {len(final_state['identified_user_wishlist'])} items potenciales.")
        # Descomentar para ver detalles de la wishlist:
        # print("   Detalles de la Wishlist:")
        # for item in final_state['identified_user_wishlist']:
        #     name = item.get('name', item.get('product_id', 'Desconocido'))
        #     print(f"     - {name} (Fuente: {item.get('source')})")
    else:
        print("📋 Wishlist Identificada: Vacía.")

    if final_state.get('user_profile'):
        print(f"👤 Perfil de Usuario: {final_state['user_profile']}")
    else:
        print("👤 Perfil de Usuario: No disponible.")

    if final_state.get('shopping_plan'):
        plan = final_state['shopping_plan']
        print("\n--- 🛍️ Plan de Compra Generado 🛍️ ---")
        print(f"💰 Presupuesto: {plan.get('budget')} {plan.get('currency', '')}")
        print(f"💳 Costo Estimado Total: {plan.get('estimated_total_cost')} {plan.get('currency', '')}")

        print("\n🛒 Items para Comprar:")
        if plan.get('items_to_buy'):
            for item in plan['items_to_buy']:
                print(f"  - {item.get('name') or item.get('marketplace_details', {}).get('name')} ({item.get('price')} {item.get('currency')}) - Fuente: {item.get('source')}")
        else:
            print("  No hay items para comprar dentro del presupuesto o disponibles.")

        print("\n🤔 Recomendaciones Adicionales/Para Después:")
        if plan.get('recommendations_for_later'):
            for rec in plan['recommendations_for_later']:
                print(f"  - {rec.get('name')}: {rec.get('reason')} {rec.get('price', '')} {plan.get('currency', '') if rec.get('price') else ''}")
        else:
            print("  No hay recomendaciones adicionales.")
    else:
        print("\n--- 🛍️ Plan de Compra Generado 🛍️ ---")
        print("  No se pudo generar el plan de compra.")

    if final_state.get('search_criteria') or final_state.get('search_results'):
        print("\n--- 🔎 Resultados de Búsqueda de Productos 🔎 ---")
        print(f"Criterios Utilizados: {final_state.get('search_criteria')}")
        results = final_state.get('search_results', [])
        if results:
            print(f"Se encontraron {len(results)} productos:")
            for prod in results:
                print(f"  - {prod.get('name')} (Precio: {prod.get('price')} {prod.get('currency')}, Stock: {prod.get('stock')}, Rating: {prod.get('ratings',{}).get('average_rating')})")
        else:
            print("No se encontraron productos que coincidan con los criterios.")
    else:
        print("\n--- 🔎 Resultados de Búsqueda de Productos 🔎 ---")
        print("No se realizó ninguna búsqueda o no hubo resultados.")

    print("\n✨ Demostración Finalizada ✨")

if __name__ == "__main__":
    run_agent_demo()
