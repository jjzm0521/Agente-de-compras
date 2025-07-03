import tkinter as tk
from src.agent.graph import create_graph, AgentState
from src.utils import data_loader
from src.gui.app import ChatApplication

def run_gui_agent():
    """
    Inicializa y ejecuta el agente de compras conversacional con una interfaz gráfica Tkinter.

    Esta función se encarga de:
    1. Crear el grafo lógico del agente.
    2. Definir el estado inicial del agente, incluyendo datos de ejemplo y perfil de usuario.
    3. Cargar datos simulados (catálogo de productos, wishlists de redes sociales, etc.).
    4. Instanciar y lanzar la aplicación de interfaz gráfica (ChatApplication).
    """
    print("🚀 Iniciando Agente de Compras Conversacional con GUI 🚀")

    # 1. Crear el grafo del agente (núcleo lógico LangGraph)
    # Este grafo define los nodos y flujos de la lógica conversacional del agente.
    agent_logic_app = create_graph()

    # 2. Definir el estado inicial para la conversación del agente.
    # Este diccionario representa el 'AgentState' y se pasará a la GUI.
    # La GUI y el grafo del agente interactuarán y modificarán este estado.
    initial_agent_state: AgentState = {
        "marketplace_products": None,       # Productos del catálogo del marketplace
        "instagram_saves": None,            # Items guardados de Instagram
        "pinterest_boards": None,           # Pines y tableros de Pinterest
        "abandoned_carts": None,            # Carritos de compra abandonados
        "identified_user_wishlist": [],     # Lista de deseos identificada inicialmente
        "user_profile": {                   # Perfil simulado del usuario
            "budget": 1000,
            "preferred_categories": ["Electrónica", "Hogar"]
        },
        "enriched_wishlist": [],            # Lista de deseos enriquecida con detalles del marketplace
        "shopping_plan": {},                # Plan de compra generado
        "search_criteria": None,            # Criterios para la búsqueda de productos
        "search_results": [],               # Resultados de la búsqueda de productos
        "ia_categorized_wishlist": None,    # Wishlist categorizada por IA (salida del WishlistAgent)
        "wishlist_agent_error": None,       # Errores del WishlistAgent
        "raw_cart_items": None,             # Items crudos del carrito (antes de procesar)
        "conversation_history": [],         # Historial de la conversación [(speaker, text), ...]
        "current_user_input": None,         # Última entrada del usuario
        "master_agent_decision": None,      # Decisión tomada por el MasterAgent (qué hacer a continuación)
        "catalog_search_output": None       # Salida de la herramienta de búsqueda en catálogo
    }

    # 3. Cargar datos iniciales simulados.
    # Estos datos son utilizados por las herramientas del agente o para poblar el estado inicial.
    print("Cargando datos iniciales para el entorno del agente...")
    try:
        initial_agent_state['marketplace_products'] = data_loader.get_marketplace_products()
        initial_agent_state['instagram_saves'] = data_loader.get_instagram_saves()
        initial_agent_state['pinterest_boards'] = data_loader.get_pinterest_boards()
        initial_agent_state['abandoned_carts'] = data_loader.get_abandoned_carts()
        print("Datos iniciales cargados correctamente.")
    except Exception as e:
        print(f"💥 Error cargando datos iniciales: {e}")
        print("El agente podría no funcionar como se espera sin los datos iniciales.")
        # La aplicación continuará, pero algunas funcionalidades pueden fallar
        # si dependen de estos datos y no se cargaron.

    # 4. Configurar y lanzar la aplicación GUI.
    # Se crea la ventana principal de Tkinter y se instancia ChatApplication.
    root = tk.Tk()
    # Se pasa el grafo del agente (agent_logic_app) y el estado inicial a la GUI.
    gui_app = ChatApplication(root, agent_app=agent_logic_app, initial_agent_state=initial_agent_state)

    print("✨ Iniciando interfaz gráfica... Por favor, interactúa con la ventana de chat. ✨")
    # root.mainloop() inicia el bucle de eventos de Tkinter, mostrando la GUI
    # y esperando la interacción del usuario. Esta llamada es bloqueante.
    root.mainloop()

    print("\n✨ Sesión de Agente Conversacional con GUI Finalizada. ¡Hasta pronto! ✨")


if __name__ == "__main__":
    # Este bloque se ejecuta cuando el script es llamado directamente (ej: python src/main.py).
    # Llama a la función principal para iniciar la aplicación.
    run_gui_agent()
