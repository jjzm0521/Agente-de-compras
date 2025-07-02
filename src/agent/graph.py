from typing import Dict, Any, List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from src.utils import data_loader
from .search_handler import search_products_node # Importar el nuevo nodo

# --- Definición del Estado del Agente ---
class AgentState(TypedDict):
    """
    Estado del agente que se pasa entre los nodos del grafo.
    """
    marketplace_products: Optional[List[Dict[str, Any]]]
    instagram_saves: Optional[Dict[str, Any]]
    pinterest_boards: Optional[Dict[str, Any]]
    abandoned_carts: Optional[List[Dict[str, Any]]]

    # Resultados del procesamiento
    identified_user_wishlist: List[Dict[str, Any]] # Lista de productos de interés para el usuario
    user_profile: Dict[str, Any] # Podría incluir presupuesto, preferencias, etc.
    enriched_wishlist: List[Dict[str, Any]] # Wishlist con productos machetados y enriquecidos del marketplace
    shopping_plan: Dict[str, Any] # Plan de compra generado

    # Para la funcionalidad de búsqueda
    search_criteria: Optional[Dict[str, Any]] # Ej: {"query": "cafetera", "max_price": 100}
    search_results: Optional[List[Dict[str, Any]]]
    # ... más campos según sea necesario

# --- Nodos del Grafo ---

def load_marketplace_data(state: AgentState) -> AgentState:
    """Nodo para cargar los productos del marketplace."""
    print("---CARGANDO DATOS DEL MARKETPLACE---")
    products = data_loader.get_marketplace_products()
    state['marketplace_products'] = products
    if products:
        print(f"Cargados {len(products)} productos del marketplace.")
    else:
        print("No se pudieron cargar los productos del marketplace.")
    return state

def load_instagram_data(state: AgentState) -> AgentState:
    """Nodo para cargar los 'saves' de Instagram."""
    print("---CARGANDO DATOS DE INSTAGRAM---")
    insta_saves = data_loader.get_instagram_saves()
    state['instagram_saves'] = insta_saves
    if insta_saves:
        print(f"Cargados {len(insta_saves.get('saved_items', []))} items de Instagram.")
    else:
        print("No se pudieron cargar los datos de Instagram.")
    return state

def load_pinterest_data(state: AgentState) -> AgentState:
    """Nodo para cargar los datos de Pinterest."""
    print("---CARGANDO DATOS DE PINTEREST---")
    pinterest_data = data_loader.get_pinterest_boards()
    state['pinterest_boards'] = pinterest_data
    if pinterest_data:
        print(f"Cargados {len(pinterest_data.get('boards', []))} tableros de Pinterest.")
    else:
        print("No se pudieron cargar los datos de Pinterest.")
    return state

def load_abandoned_carts_data(state: AgentState) -> AgentState:
    """Nodo para cargar los carritos abandonados."""
    print("---CARGANDO DATOS DE CARRITOS ABANDONADOS---")
    carts = data_loader.get_abandoned_carts()
    state['abandoned_carts'] = carts
    if carts:
        print(f"Cargados {len(carts)} carritos abandonados.")
    else:
        print("No se pudieron cargar los carritos abandonados.")
    return state

def initial_data_processing(state: AgentState) -> AgentState:
    """
    Nodo para un procesamiento inicial de los datos cargados.
    Por ahora, solo imprimirá un resumen. Más adelante, aquí se identificarán
    productos de interés, se unificarán, etc.
    """
    print("---PROCESANDO DATOS INICIALES---")
    wishlist = []

    # Ejemplo simple: extraer nombres de productos detectados en Instagram
    if state.get('instagram_saves') and state['instagram_saves'].get('saved_items'):
        for item in state['instagram_saves']['saved_items']:
            if item.get('detected_product_name'):
                wishlist.append({
                    "source": "instagram",
                    "name": item['detected_product_name'],
                    "details": item
                })

    # Ejemplo simple: extraer nombres de productos detectados en Pinterest
    if state.get('pinterest_boards') and state['pinterest_boards'].get('boards'):
        for board in state['pinterest_boards']['boards']:
            for pin in board.get('pins', []):
                if pin.get('detected_product_name'):
                    wishlist.append({
                        "source": "pinterest",
                        "name": pin['detected_product_name'],
                        "details": pin
                    })

    # Ejemplo simple: extraer product_ids de carritos abandonados
    if state.get('abandoned_carts'):
        for cart in state['abandoned_carts']:
            for item in cart.get('items', []):
                wishlist.append({
                    "source": "abandoned_cart",
                    "product_id": item.get('product_id'),
                    "details": item
                })

    state['identified_user_wishlist'] = wishlist
    print(f"Identificados {len(wishlist)} items de interés iniciales.")
    # Inicializar otros campos del estado si es necesario
    if 'user_profile' not in state or state['user_profile'] is None:
        state['user_profile'] = {}
    if 'enriched_wishlist' not in state or state['enriched_wishlist'] is None:
        state['enriched_wishlist'] = []
    if 'shopping_plan' not in state or state['shopping_plan'] is None:
        state['shopping_plan'] = {}
    if 'search_criteria' not in state: # No sobrescribir si ya existe
        state['search_criteria'] = None
    if 'search_results' not in state:
        state['search_results'] = None
    return state

def product_matching_and_enrichment(state: AgentState) -> AgentState:
    """
    Intenta hacer coincidir productos de la wishlist con el catálogo del marketplace
    y enriquece la información.
    """
    print("---REALIZANDO MATCHING Y ENRIQUECIMIENTO DE PRODUCTOS---")
    enriched_items = []
    marketplace_products = state.get('marketplace_products', [])
    identified_wishlist = state.get('identified_user_wishlist', [])

    if not marketplace_products:
        print("Advertencia: No hay productos del marketplace para hacer matching.")
        state['enriched_wishlist'] = identified_wishlist # Pasar la wishlist sin enriquecer
        return state

    for item in identified_wishlist:
        matched_product = None
        # Intento de matching muy básico:
        # 1. Por product_id si existe (ej: de carritos abandonados)
        # 2. Por nombre detectado (puede ser impreciso)
        if item.get('product_id'):
            for mp_item in marketplace_products:
                if mp_item['id'] == item['product_id']:
                    matched_product = mp_item
                    break
        elif item.get('name'): # Matching por nombre (sensible a mayúsculas/minúsculas y variaciones)
            for mp_item in marketplace_products:
                if item['name'].lower() in mp_item['name'].lower() or mp_item['name'].lower() in item['name'].lower():
                    matched_product = mp_item
                    break

        enriched_item = item.copy()
        if matched_product:
            enriched_item['marketplace_details'] = matched_product
            enriched_item['price'] = matched_product.get('price')
            enriched_item['currency'] = matched_product.get('currency')
            enriched_item['in_stock'] = matched_product.get('stock', 0) > 0
            print(f"Producto '{item.get('name') or item.get('product_id')}' macheado con '{matched_product['name']}'")
        else:
            enriched_item['marketplace_details'] = None
            enriched_item['price'] = None # O un precio estimado si tuviéramos otra fuente
            enriched_item['in_stock'] = False
            print(f"Producto '{item.get('name') or item.get('product_id')}' no encontrado en el marketplace.")

        enriched_items.append(enriched_item)

    state['enriched_wishlist'] = enriched_items
    print(f"Total de items en wishlist enriquecida: {len(enriched_items)}")
    return state

def generate_shopping_plan(state: AgentState) -> AgentState:
    """
    Genera un plan de compra basado en la wishlist enriquecida y el perfil del usuario.
    """
    print("---GENERANDO PLAN DE COMPRA---")
    enriched_wishlist = state.get('enriched_wishlist', [])
    user_profile = state.get('user_profile', {})
    budget = user_profile.get('budget')  # Puede ser None

    # Prioridad 1: Items de carritos abandonados que estén en stock
    # Prioridad 2: Otros items de la wishlist que estén en stock

    items_to_buy = []
    current_cost = 0
    recommendations = [] # Productos que no entran en el presupuesto pero podrían interesar

    # Ordenar wishlist: primero carritos abandonados, luego por precio (si disponible) o simplemente como vienen
    def sort_key(item):
        is_abandoned_cart = item.get('source') == 'abandoned_cart'
        has_price = item.get('price') is not None
        # Queremos True (abandonado) antes que False, y precios más bajos antes si no es abandonado
        return (not is_abandoned_cart, not has_price, item.get('price', float('inf')))

    sorted_wishlist = sorted(enriched_wishlist, key=sort_key)

    for item in sorted_wishlist:
        if item.get('marketplace_details') and item.get('in_stock'):
            price = item.get('price')
            if price is None: # No se puede comprar si no sabemos el precio
                recommendations.append({
                    "name": item.get('name') or item.get('marketplace_details',{}).get('name'),
                    "reason": "Precio no disponible. Investigar."
                })
                continue

            if budget is None or (current_cost + price <= budget):
                items_to_buy.append(item)
                current_cost += price
            else:
                recommendations.append({
                    "name": item.get('name') or item.get('marketplace_details',{}).get('name'),
                    "price": price,
                    "reason": "Excede el presupuesto actual, pero podría interesarte para el futuro."
                })
        elif item.get('marketplace_details') and not item.get('in_stock'):
             recommendations.append({
                "name": item.get('name') or item.get('marketplace_details',{}).get('name'),
                "reason": "Actualmente fuera de stock. Guardar para más tarde."
            })
        # Si no tiene marketplace_details, es un item no macheado, podría ir a una lista de "buscar manualmente"
        elif not item.get('marketplace_details') and item.get('name'):
            recommendations.append({
                "name": item.get('name'),
                "reason": "No se encontró automáticamente en el marketplace. Podrías buscarlo manualmente."
            })


    shopping_plan = {
        "budget": budget,
        "estimated_total_cost": current_cost,
        "items_to_buy": items_to_buy,
        "recommendations_for_later": recommendations,
        "currency": items_to_buy[0].get('currency') if items_to_buy else None # Asume misma moneda
    }

    state['shopping_plan'] = shopping_plan
    print(f"Plan de compra generado con {len(items_to_buy)} items para comprar.")
    print(f"Costo total estimado: {current_cost} {shopping_plan['currency'] if shopping_plan['currency'] else ''}")
    print(f"{len(recommendations)} recomendaciones adicionales generadas.")
    return state

# --- Construcción del Grafo ---
def create_graph():
    """Crea y configura el grafo del agente."""
    workflow = StateGraph(AgentState)

    # Añadir nodos
    workflow.add_node("load_marketplace", load_marketplace_data)
    workflow.add_node("load_instagram", load_instagram_data)
    workflow.add_node("load_pinterest", load_pinterest_data)
    workflow.add_node("load_carts", load_abandoned_carts_data)
    workflow.add_node("initial_processing", initial_data_processing)
    workflow.add_node("product_matching", product_matching_and_enrichment)
    workflow.add_node("generate_plan", generate_shopping_plan)

    # Definir el flujo
    workflow.set_entry_point("load_marketplace")
    workflow.add_edge("load_marketplace", "load_instagram")
    workflow.add_edge("load_instagram", "load_pinterest")
    workflow.add_edge("load_pinterest", "load_carts")
    workflow.add_edge("load_carts", "initial_processing")
    workflow.add_edge("initial_processing", "product_matching")
    workflow.add_edge("product_matching", "generate_plan")
    # workflow.add_edge("generate_plan", END) # Ya no es el final si queremos permitir búsqueda después

    # Nuevo nodo de búsqueda y flujo condicional (o secuencial por ahora)
    workflow.add_node("search_products", search_products_node)

    # Flujo: Después de generar el plan, va al nodo de búsqueda.
    # Más adelante, esto podría ser condicional o un punto de entrada diferente.
    workflow.add_edge("generate_plan", "search_products")
    workflow.add_edge("search_products", END)

    # Compilar el grafo
    app = workflow.compile()
    return app

if __name__ == '__main__':
    app = create_graph()

    # Ejecutar el grafo con un estado inicial vacío o predefinido
    initial_state = {
        "identified_user_wishlist": [],
        "user_profile": {"budget": 500, "preferred_categories": ["Electrónica"]} # Ejemplo
    }

    # Imprimir la imagen del grafo para visualización (requiere graphviz)
    try:
        # Guardar la imagen del grafo
        app.get_graph().draw_mermaid_png(output_file_path="graph_visualization.png")
        print("\nVisualización del grafo guardada como graph_visualization.png (si graphviz está instalado)")
    except Exception as e:
        print(f"\nNo se pudo generar la visualización del grafo (requiere graphviz): {e}")

    print("\n---EJECUTANDO GRAFO---")
    final_state = app.invoke(initial_state)

    print("\n---ESTADO FINAL DEL AGENTE---")
    # Imprimir selectivamente para no saturar la consola si los datos son grandes
    print(f"Productos del Marketplace: {len(final_state.get('marketplace_products', []))} items")
    print(f"Saves de Instagram: {len(final_state.get('instagram_saves', {}).get('saved_items', []))} items")
    print(f"Tableros de Pinterest: {len(final_state.get('pinterest_boards', {}).get('boards', []))} tableros")
    print(f"Carritos Abandonados: {len(final_state.get('abandoned_carts', []))} carritos")
    print(f"Wishlist Identificada: {len(final_state.get('identified_user_wishlist', []))} items")
    # print("\nWishlist detallada:")
    # for item in final_state.get('identified_user_wishlist', []):
    #     print(f"  - {item.get('name') or item.get('product_id')} (Fuente: {item.get('source')})")
    print(f"Perfil de Usuario: {final_state.get('user_profile')}")
