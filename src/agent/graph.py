from typing import Dict, Any, List, TypedDict, Optional, TYPE_CHECKING
from langchain_core.prompts import ChatPromptTemplate
#from langchain_core.pydantic_v1 import BaseModel, Field as PydanticField # Ya no se necesita aquí
from langgraph.graph import StateGraph, END
import os # Para getenv en generate_shopping_plan

from src.utils import data_loader
from src.utils.config import get_llm
from .search_handler import search_products_node
from .wishlist_agent import run_wishlist_agent
from .planner_models import PurchaseAdvice, SHOPPING_ADVICE_PROMPT_TEMPLATE # Importar modelos y prompt

if TYPE_CHECKING: # Evitar importación circular, aunque planner_models no importa graph
    pass

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

    # Para el WishlistAgent con IA
    ia_categorized_wishlist: Optional[List[Dict[str, Any]]] # Resultados del WishlistAgent
    wishlist_agent_error: Optional[str] # Para capturar errores del WishlistAgent

    raw_cart_items: Optional[List[Dict[str, Any]]] # Items de carritos procesados antes del matching
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
    if 'raw_cart_items' not in state: # Nuevo campo
        state['raw_cart_items'] = []
    if 'ia_categorized_wishlist' not in state: # Nuevo campo
        state['ia_categorized_wishlist'] = []
    if 'wishlist_agent_error' not in state: # Nuevo campo
        state['wishlist_agent_error'] = None
    return state

# El nodo initial_data_processing se elimina. Su funcionalidad de extracción simple
# es reemplazada por run_wishlist_agent para items de redes sociales
# y un nuevo nodo extract_cart_data para los carritos.

# Nuevo nodo para procesar carritos abandonados y prepararlos para el matching
def extract_cart_data(state: AgentState) -> AgentState:
    """
    Extrae items de carritos abandonados y los formatea para el proceso de matching.
    Estos items no pasan por el LLM en esta fase.
    """
    print("---EXTRAYENDO DATOS DE CARRITOS ABANDONADOS (PARA MATCHING DIRECTO)---")
    abandoned_carts_data = state.get('abandoned_carts', []) # Cargado por load_abandoned_carts_data
    processed_cart_items = []
    if abandoned_carts_data:
        for cart in abandoned_carts_data:
            for item in cart.get('items', []):
                # Guardamos la información original del item del carrito, más la fuente.
                processed_cart_items.append({
                    **item, # product_id, quantity, added_at
                    "source": "abandoned_cart",
                    "cart_id": cart.get('cart_id'),
                    "user_id": cart.get('user_id')
                })
    state['raw_cart_items'] = processed_cart_items
    print(f"Extraídos {len(processed_cart_items)} items de carritos abandonados para matching directo.")
    return state

def product_matching_and_enrichment(state: AgentState) -> AgentState:
    """
    Intenta hacer coincidir productos de ia_categorized_wishlist (proveniente del WishlistAgent)
    y raw_cart_items con el catálogo del marketplace y enriquece la información.
    """
    print("---REALIZANDO MATCHING Y ENRIQUECIMIENTO DE PRODUCTOS (POST-IA Y CARRITOS)---")
    enriched_items_final = []
    marketplace_products = state.get('marketplace_products', [])

    ia_wishlist = state.get('ia_categorized_wishlist', [])
    raw_cart_items = state.get('raw_cart_items', [])

    if not marketplace_products:
        print("Advertencia: No hay productos del marketplace para hacer matching.")
        # Combinar ia_wishlist y raw_cart_items (formateando raw_cart_items para que se parezcan)
        # y devolverlos sin detalles del marketplace.
        all_items_without_match = ia_wishlist # ya están en formato CategorizedItem (como dict)
        for cart_item_info in raw_cart_items:
            all_items_without_match.append({
                'original_text': f"Item de carrito: ID {cart_item_info.get('product_id')}",
                'identified_product_name': f"ID {cart_item_info.get('product_id')}",
                'category': "Desconocida", 'key_features': [],
                'user_sentiment_or_intent': 'abandono de carrito',
                'source': cart_item_info.get('source', 'abandoned_cart'),
                'original_item_details': cart_item_info,
                'marketplace_details': None, 'price': None, 'in_stock': False
            })
        state['enriched_wishlist'] = all_items_without_match
        return state

    # 1. Procesar items de la ia_categorized_wishlist (Instagram, Pinterest)
    print(f"Procesando {len(ia_wishlist)} items de la IA Wishlist para matching...")
    for ia_item_dict in ia_wishlist: # ia_item_dict es un dict del modelo CategorizedItem
        matched_product = None
        product_name_from_ia = ia_item_dict.get('identified_product_name')

        if product_name_from_ia:
            category_from_ia = ia_item_dict.get('category', '').lower()

            best_match = None
            weak_match = None

            for mp_item in marketplace_products:
                mp_name_lower = mp_item['name'].lower()
                mp_category_lower = mp_item.get('category', '').lower()

                name_match = product_name_from_ia.lower() in mp_name_lower or \
                             mp_name_lower in product_name_from_ia.lower()

                if name_match:
                    if category_from_ia and mp_category_lower and category_from_ia == mp_category_lower:
                        best_match = mp_item # Match fuerte (nombre y categoría)
                        break # Tomar el primer match fuerte
                    elif not weak_match: # Si aún no tenemos un match débil
                        weak_match = mp_item # Guardar como match débil (solo nombre, o categoría no coincide/falta)

            if best_match:
                matched_product = best_match
            elif weak_match:
                matched_product = weak_match # Usar match débil si no hubo fuerte
                if category_from_ia and matched_product.get('category') and category_from_ia != matched_product.get('category','').lower():
                    print(f"Info: Producto IA '{product_name_from_ia}' (Cat IA: {ia_item_dict.get('category')}) macheado con '{matched_product['name']}' (Cat MP: {matched_product.get('category')}) por nombre, pero categorías difieren.")
            # else: matched_product sigue siendo None

        # ia_item_dict ya tiene la estructura base de CategorizedItem
        # Solo necesitamos añadir/actualizar los detalles del marketplace
        enriched_item_from_ia = ia_item_dict.copy()
        if matched_product:
            enriched_item_from_ia['marketplace_details'] = matched_product
            enriched_item_from_ia['price'] = matched_product.get('price')
            enriched_item_from_ia['currency'] = matched_product.get('currency')
            enriched_item_from_ia['in_stock'] = matched_product.get('stock', 0) > 0
            print(f"Producto IA '{product_name_from_ia}' macheado con '{matched_product['name']}'")
        else:
            enriched_item_from_ia['marketplace_details'] = None # Asegurar que esté explícitamente
            enriched_item_from_ia['price'] = None
            enriched_item_from_ia['in_stock'] = False
            print(f"Producto IA '{product_name_from_ia}' no encontrado en el marketplace.")
        enriched_items_final.append(enriched_item_from_ia)

    # 2. Procesar items de raw_cart_items (Carritos Abandonados)
    print(f"Procesando {len(raw_cart_items)} items de carritos abandonados para matching...")
    for cart_item_info in raw_cart_items:
        matched_product = None
        product_id = cart_item_info.get('product_id')

        # Crear una estructura base similar a CategorizedItem para consistencia
        cart_item_for_enrichment = {
            'original_text': f"Item de carrito: ID {product_id}, Cantidad: {cart_item_info.get('quantity',1)}",
            'identified_product_name': f"Producto ID: {product_id}", # Placeholder, se actualizará si hay match
            'category': "Desconocida", # Placeholder
            'key_features': [],
            'user_sentiment_or_intent': 'producto en carrito abandonado',
            'source': cart_item_info.get('source', 'abandoned_cart'),
            'original_item_details': cart_item_info,
            'marketplace_details': None,
            'price': None,
            'in_stock': False
        }

        if product_id:
            for mp_item in marketplace_products:
                if mp_item['id'] == product_id:
                    matched_product = mp_item
                    break

        if matched_product:
            cart_item_for_enrichment['identified_product_name'] = matched_product.get('name')
            cart_item_for_enrichment['category'] = matched_product.get('category')
            cart_item_for_enrichment['marketplace_details'] = matched_product
            cart_item_for_enrichment['price'] = matched_product.get('price')
            cart_item_for_enrichment['currency'] = matched_product.get('currency')
            cart_item_for_enrichment['in_stock'] = matched_product.get('stock', 0) > 0
            print(f"Item de carrito ID '{product_id}' macheado con '{matched_product['name']}'")
        else:
            print(f"Item de carrito ID '{product_id}' no encontrado en el marketplace.")
        enriched_items_final.append(cart_item_for_enrichment)

    state['enriched_wishlist'] = enriched_items_final
    print(f"Total de items en wishlist enriquecida (IA + Carritos): {len(enriched_items_final)}")
    return state

def generate_shopping_plan(state: AgentState) -> AgentState:
    """
    Genera un plan de compra basado en la wishlist enriquecida y el perfil del usuario.
    También intenta generar consejos de compra personalizados usando un LLM para algunos items.
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
    print(f"Plan de compra generado con {len(items_to_buy)} items para comprar (antes de consejos IA).")
    print(f"Costo total estimado: {current_cost} {shopping_plan['currency'] if shopping_plan['currency'] else ''}")
    print(f"{len(recommendations)} recomendaciones adicionales generadas.")

    # --- Tarea IA: Generar consejo para algunos items ---
    if items_to_buy: # Solo si hay items para comprar
        try:
            llm = get_llm(temperature=0.7, model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")) # Temp más alta para creatividad

            advice_prompt = ChatPromptTemplate.from_template(SHOPPING_ADVICE_PROMPT_TEMPLATE)
            advice_chain = advice_prompt | llm.with_structured_output(PurchaseAdvice)

            items_with_advice = []
            # Generar consejo para los primeros N items (ej. 2)
            # Asegurarse de que los items tengan la info necesaria para el prompt
            for i, item_to_advise in enumerate(items_to_buy):
                if i >= 2: # Limitar a 2 items por ahora
                    items_with_advice.append(item_to_advise) # Añadir el resto sin consejo
                    continue

                product_name = item_to_advise.get('identified_product_name', 'Producto desconocido')
                marketplace_details = item_to_advise.get('marketplace_details', {})

                item_payload = {
                    "product_name": product_name,
                    "product_category": item_to_advise.get('category', marketplace_details.get('category', 'No especificada')),
                    "product_price": str(item_to_advise.get('price', marketplace_details.get('price', 'N/A'))),
                    "product_currency": item_to_advise.get('currency', marketplace_details.get('currency', '')),
                    "key_features": ", ".join(item_to_advise.get('key_features', [])[:3]), # Primeras 3 características
                    "source": item_to_advise.get('source', 'desconocida'),
                    "user_sentiment": item_to_advise.get('user_sentiment_or_intent', 'interés general')
                }

                try:
                    print(f"Generando consejo IA para: {product_name}")
                    advice_response = advice_chain.invoke(item_payload)
                    # Añadir el consejo al item
                    item_copy = item_to_advise.copy()
                    item_copy['purchase_advice'] = advice_response.advice
                    items_with_advice.append(item_copy)
                    print(f"Consejo para '{advice_response.item_name}': {advice_response.advice}")
                except Exception as e_advice:
                    print(f"Error generando consejo IA para '{product_name}': {e_advice}")
                    items_with_advice.append(item_to_advise) # Añadir sin consejo si falla

            shopping_plan['items_to_buy'] = items_with_advice # Actualizar con los consejos
            print("Consejos de IA añadidos al plan de compra.")

        except ValueError as e_llm: # Error al obtener LLM (API key)
            print(f"Error al inicializar LLM para consejos de compra: {e_llm}. No se añadirán consejos IA.")
        except Exception as e_gen:
            print(f"Error inesperado durante la generación de consejos IA: {e_gen}. No se añadirán consejos IA.")

    state['shopping_plan'] = shopping_plan
    return state

# SHOPPING_ADVICE_PROMPT_TEMPLATE y PurchaseAdvice ahora se importan de .planner_models

# --- Construcción del Grafo ---
def create_graph():
    """Crea y configura el grafo del agente."""
    workflow = StateGraph(AgentState)

    # Añadir nodos
    workflow.add_node("load_marketplace", load_marketplace_data)
    workflow.add_node("load_instagram", load_instagram_data)
    workflow.add_node("load_pinterest", load_pinterest_data)
    workflow.add_node("load_carts", load_abandoned_carts_data) # Carga los datos crudos de carritos

    workflow.add_node("wishlist_analyzer_node", run_wishlist_agent) # Nuevo: Analiza Instagram y Pinterest con IA
    workflow.add_node("extract_cart_data_node", extract_cart_data) # Nuevo: Procesa carritos para matching directo

    workflow.add_node("product_matching", product_matching_and_enrichment) # Modificado: Usa salida de IA y carritos procesados
    workflow.add_node("generate_plan", generate_shopping_plan)
    workflow.add_node("search_products", search_products_node)

    # Definir el flujo
    # 1. Cargar todos los datos
    workflow.set_entry_point("load_marketplace")
    workflow.add_edge("load_marketplace", "load_instagram")
    workflow.add_edge("load_instagram", "load_pinterest")
    workflow.add_edge("load_pinterest", "load_carts")

    # 2. Después de cargar todo, procesar en paralelo (o secuencialmente si es más simple por ahora)
    #    los items de redes sociales con IA y los items de carritos.
    #    Para LangGraph, los flujos paralelos se manejan con múltiples aristas desde un nodo
    #    o usando un nodo "router" condicional. Por simplicidad, haremos un flujo secuencial
    #    donde el WishlistAgent opera sobre los datos de redes sociales, y extract_cart_data
    #    opera sobre los datos de carritos. Ambos resultados alimentarán el nodo de matching.

    workflow.add_edge("load_carts", "wishlist_analyzer_node") # WishlistAnalyzer usa datos de Insta/Pin
    workflow.add_edge("wishlist_analyzer_node", "extract_cart_data_node") # Luego procesar carritos
    workflow.add_edge("extract_cart_data_node", "product_matching") # Matching usa ambos resultados

    # 3. Continuar con el flujo existente
    workflow.add_edge("product_matching", "generate_plan")
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
