import tkinter as tk
from src.agent.graph import create_graph, AgentState
from src.utils import data_loader # Asegurar que data_loader se importa globalmente si es necesario
from src.gui.app import ChatApplication # Importar la clase de la GUI

def run_gui_agent():
    """
    Ejecuta el agente de compras conversacional con una interfaz gráfica Tkinter.
    """
    print("🚀 Iniciando Agente de Compras Conversacional con GUI 🚀")

    # Crear el grafo del agente (núcleo lógico)
    agent_logic_app = create_graph()

    # Estado inicial para la conversación del agente
    # Este estado se pasará a la GUI y se actualizará allí.
    initial_agent_state: AgentState = {
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
        "conversation_history": [],
        "current_user_input": None,
        "master_agent_decision": None,
        "catalog_search_output": None
    }

    # Cargar datos iniciales que el agente podría necesitar a través de sus herramientas
    # o directamente en el estado si así está diseñado.
    print("Cargando datos iniciales para el entorno del agente...")
    try:
        initial_agent_state['marketplace_products'] = data_loader.get_marketplace_products()
        initial_agent_state['instagram_saves'] = data_loader.get_instagram_saves()
        initial_agent_state['pinterest_boards'] = data_loader.get_pinterest_boards()
        initial_agent_state['abandoned_carts'] = data_loader.get_abandoned_carts()
        print("Datos iniciales cargados.")
    except Exception as e:
        print(f"💥 Error cargando datos iniciales: {e}")
        # Decidir si continuar sin datos o terminar. Por ahora, informamos y continuamos.
        # La GUI mostrará un error si el agente intenta acceder a datos no cargados.

    # Configurar y lanzar la aplicación GUI
    root = tk.Tk()
    gui_app = ChatApplication(root, agent_app=agent_logic_app, initial_agent_state=initial_agent_state)

    print("✨ Iniciando interfaz gráfica... ✨")
    root.mainloop() # Esto bloquea hasta que la ventana de Tkinter se cierre

    print("\n✨ Sesión de Agente Conversacional con GUI Finalizada ✨")


if __name__ == "__main__":
    # No es necesario importar data_loader aquí si ya está en el scope global o importado arriba.
    # from src.utils import data_loader # Ya está importado arriba
    run_gui_agent() # Llamar a la función que inicia la GUI
