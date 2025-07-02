import json
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field # <--- CAMBIO AQUÍ

from src.utils.config import get_llm
from src.utils.data_loader import get_instagram_saves, get_pinterest_boards

# --- Pydantic Modelos para la Salida Estructurada del LLM ---
class CategorizedItem(BaseModel):
    original_text: str = Field(description="El texto original del post o pin.")
    identified_product_name: Optional[str] = Field(description="El nombre del producto o servicio identificado en el texto. Si no se identifica un producto claro, puede ser una descripción breve del objeto de deseo.")
    category: Optional[str] = Field(description="Categoría estimada para el producto/servicio (ej: Electrónica, Ropa, Hogar, Viajes, Comida, Libros, Belleza, Deporte, Otro).")
    key_features: List[str] = Field(description="Una lista de características clave, palabras clave o atributos mencionados sobre el producto/servicio.")
    user_sentiment_or_intent: Optional[str] = Field(description="Sentimiento o intención del usuario hacia el item (ej: deseo fuerte, consideración, necesita oferta, inspiración).")
    source: str = Field(description="La fuente original del item (ej: 'instagram', 'pinterest').")
    original_item_details: Dict[Any, Any] = Field(description="Detalles completos del item original de la fuente.")

class WishlistAnalysisResult(BaseModel):
    categorized_items: List[CategorizedItem] = Field(description="Lista de items analizados y categorizados por el LLM.")


# --- Prompts ---
WISHLIST_ANALYSIS_PROMPT_TEMPLATE = """
Eres un asistente experto en analizar listas de deseos de redes sociales.
Tu tarea es analizar el siguiente item de una lista de deseos (proveniente de {source}) y extraer información relevante.

Texto del item:
---
{text_input}
---

Por favor, extrae la siguiente información y formatea tu respuesta como un objeto JSON que se ajuste al esquema de `CategorizedItem`:
- `identified_product_name`: El nombre del producto o servicio que el usuario parece desear. Si no es un producto específico, describe brevemente el objeto de deseo.
- `category`: La categoría más apropiada para este producto/servicio. Elige entre: Electrónica, Ropa, Hogar, Viajes, Comida, Libros, Belleza, Deporte, Otro.
- `key_features`: Una lista de 2-4 características clave, palabras clave o atributos mencionados.
- `user_sentiment_or_intent`: Describe brevemente el sentimiento o la intención del usuario (ej: "deseo fuerte", "consideración casual", "buscando oferta", "inspiración general", "necesidad específica").

Contexto adicional del item original (solo para tu referencia, no lo incluyas directamente en la respuesta a menos que sea parte del análisis):
{original_details_str}

Responde ÚNICAMENTE con el objeto JSON que se adhiere al esquema de `CategorizedItem`. No incluyas explicaciones adicionales ni texto introductorio.
El objeto JSON debe tener las siguientes claves (con sus respectivos tipos):
- original_text: str (el texto original proporcionado)
- identified_product_name: Optional[str]
- category: Optional[str]
- key_features: List[str]
- user_sentiment_or_intent: Optional[str]
- source: str (la fuente proporcionada: '{source}')
- original_item_details: Dict (los detalles originales proporcionados)

Ejemplo de cómo se vería el JSON (sin las comillas triples externas):
```json
{{
  "original_text": "¡Me encantan estos nuevos auriculares! #AudioMax #ProSound #GadgetGoals",
  "identified_product_name": "Auriculares ProSound de AudioMax",
  "category": "Electrónica",
  "key_features": ["auriculares", "ProSound", "AudioMax", "GadgetGoals"],
  "user_sentiment_or_intent": "deseo fuerte",
  "source": "instagram",
  "original_item_details": {{ "post_id": "INSTA_POST_001", "image_url": "..." }}
}}
```
"""

# --- Funciones del Agente ---
def analyze_social_media_item(llm, item_text: str, source: str, original_item_data: Dict) -> Optional[CategorizedItem]:
    """
    Analiza un solo item de red social usando el LLM para extraer y categorizar información.
    """
    prompt = ChatPromptTemplate.from_template(WISHLIST_ANALYSIS_PROMPT_TEMPLATE)

    # Crear una cadena LangChain con el LLM, el prompt y el parser de salida Pydantic
    # Usaremos .with_structured_output para que Langchain maneje el parsing al modelo Pydantic
    chain = prompt | llm.with_structured_output(CategorizedItem)

    try:
        response = chain.invoke({
            "source": source,
            "text_input": item_text,
            "original_details_str": json.dumps(original_item_data, indent=2) # Para el contexto del LLM
        })
        # El response ya debería ser un objeto CategorizedItem gracias a with_structured_output
        # Solo necesitamos asegurarnos de que los campos `original_text`, `source` y `original_item_details`
        # que el LLM no genera directamente, se rellenen correctamente.
        # El LLM SÍ debe generar `source` según el prompt, pero lo forzamos por si acaso.
        # `original_text` y `original_item_details` también se le piden al LLM,
        # pero es más seguro llenarlos aquí con los datos exactos que pasamos.

        # El prompt ahora le pide al LLM que incluya estos campos.
        # response.original_text = item_text # El LLM debería incluirlo
        # response.source = source # El LLM debería incluirlo
        # response.original_item_details = original_item_data # El LLM debería incluirlo

        return response
    except Exception as e:
        print(f"Error analizando item con LLM: {e}")
        print(f"Item problemático (texto): {item_text[:100]}...") # Imprimir solo una parte
        return None

def run_wishlist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del grafo para el WishlistAgent.
    Toma los datos cargados de Instagram y Pinterest, los analiza con un LLM,
    y actualiza el estado con la 'ia_categorized_wishlist'.
    """
    print("--- EJECUTANDO WISHLIST AGENT (Análisis y Categorización con IA) ---")

    # Obtener LLM (esto fallará si la API key no está configurada)
    try:
        llm = get_llm(temperature=0.1) # Usar baja temperatura para respuestas más consistentes
    except ValueError as e:
        print(f"Error crítico al inicializar LLM para WishlistAgent: {e}")
        print("El WishlistAgent no puede continuar sin un LLM configurado.")
        # Devolver el estado sin cambios o con una lista vacía para indicar fallo
        state['ia_categorized_wishlist'] = []
        state['wishlist_agent_error'] = str(e)
        return state

    instagram_data = state.get('instagram_saves')
    pinterest_data = state.get('pinterest_boards')

    # Si no se cargaron previamente, intentar cargarlos ahora.
    # En un flujo multi-agente más robusto, la carga sería responsabilidad de otro agente o un paso previo.
    if not instagram_data:
        instagram_data = get_instagram_saves()
        state['instagram_saves'] = instagram_data # Actualizar estado si se cargó aquí

    if not pinterest_data:
        pinterest_data = get_pinterest_boards()
        state['pinterest_boards'] = pinterest_data # Actualizar estado si se cargó aquí

    analyzed_items: List[CategorizedItem] = []

    # Analizar Instagram Saves
    if instagram_data and instagram_data.get('saved_items'):
        print(f"Analizando {len(instagram_data['saved_items'])} items de Instagram...")
        for item in instagram_data['saved_items']:
            text_to_analyze = item.get('caption', '')
            if not text_to_analyze:
                print(f"Skipping Instagram item {item.get('post_id')} due to empty caption.")
                continue

            # Pasar el item completo como original_item_details
            categorized_item = analyze_social_media_item(llm, text_to_analyze, "instagram", item)
            if categorized_item:
                analyzed_items.append(categorized_item)
    else:
        print("No hay datos de Instagram para analizar o ya fueron procesados.")

    # Analizar Pinterest Pins
    if pinterest_data and pinterest_data.get('boards'):
        print("Analizando items de Pinterest...")
        for board in pinterest_data['boards']:
            for pin in board.get('pins', []):
                text_to_analyze = pin.get('description', '')
                if not text_to_analyze:
                    print(f"Skipping Pinterest pin {pin.get('pin_id')} due to empty description.")
                    continue

                # Pasar el pin completo como original_item_details
                categorized_item = analyze_social_media_item(llm, text_to_analyze, "pinterest", pin)
                if categorized_item:
                    analyzed_items.append(categorized_item)
    else:
        print("No hay datos de Pinterest para analizar o ya fueron procesados.")

    # TODO: Considerar también analizar 'abandoned_carts' si queremos aplicar IA aquí.
    # Por ahora, los carritos abandonados ya tienen product_ids, por lo que el matching es más directo.
    # El LLM podría usarse para inferir por qué se abandonó el carrito si hubiera más contexto.

    state['ia_categorized_wishlist'] = [item.dict() for item in analyzed_items] # Guardar como dicts en el estado
    print(f"WishlistAgent: {len(analyzed_items)} items analizados y categorizados por IA.")
    if 'wishlist_agent_error' in state: # Limpiar error si todo fue bien
        del state['wishlist_agent_error']

    return state

# Para pruebas directas del agente
if __name__ == '__main__':
    import json
    # Crear un estado simulado para probar
    mock_state = {
        "instagram_saves": {
            "user_id": "test_insta_user",
            "saved_items": [
                {"post_id": "IG001", "caption": "Amo esta nueva laptop super rápida para gaming! #tech #laptop", "image_url": "url1"},
                {"post_id": "IG002", "caption": "Qué bonitas zapatillas para correr. Las necesito.", "image_url": "url2"},
                {"post_id": "IG003", "caption": "Unas vacaciones en la playa serían geniales ahora mismo...", "image_url": "url3"}
            ]
        },
        "pinterest_boards": {
            "user_id": "test_pin_user",
            "boards": [{
                "board_id": "B01", "board_name": "Gadgets",
                "pins": [
                    {"pin_id": "P001", "description": "El mejor smartwatch para monitorear salud y ejercicio", "link": "link1"},
                    {"pin_id": "P002", "description": "Ideas para decorar la sala con un estilo minimalista.", "link": "link2"}
                ]
            }]
        }
        # Para probar el WishlistAgent sin una API key válida, puedes mockear get_llm
        # o esperar el error de configuración.
    }
    print("Ejecutando prueba del WishlistAgent (requiere API Key de OpenAI configurada en .env)...")

    # Necesitamos asegurarnos de que .env se pueda cargar desde la ubicación correcta
    # Si ejecutas `python src/agent/wishlist_agent.py` directamente:
    current_dir = os.path.basename(os.getcwd())
    if current_dir == "agent": # Si estamos en src/agent/
        os.chdir(os.path.join("..", "..")) # Moverse a la raíz del proyecto
        print(f"Cambiado el directorio a: {os.getcwd()} para encontrar .env")
    elif current_dir == "src": # Si estamos en src/
        os.chdir("..") # Moverse a la raíz del proyecto
        print(f"Cambiado el directorio a: {os.getcwd()} para encontrar .env")

    updated_state = run_wishlist_agent(mock_state)

    print("\n--- Estado Actualizado por WishlistAgent ---")
    if updated_state.get('wishlist_agent_error'):
        print(f"Error del WishlistAgent: {updated_state['wishlist_agent_error']}")

    print("Wishlist Categorizada por IA:")
    for item_dict in updated_state.get('ia_categorized_wishlist', []):
        # Convertir de nuevo a Pydantic model para una impresión más bonita o para validación
        item_model = CategorizedItem(**item_dict)
        print(json.dumps(item_model.dict(), indent=2, ensure_ascii=False))

    # Ejemplo de cómo se vería la salida si el LLM funciona:
    # (Esto es solo una simulación del output esperado, el LLM real puede variar)
    # {
    #   "original_text": "Amo esta nueva laptop super rápida para gaming! #tech #laptop",
    #   "identified_product_name": "Laptop para gaming",
    #   "category": "Electrónica",
    #   "key_features": ["rápida", "gaming", "tech", "laptop"],
    #   "user_sentiment_or_intent": "deseo fuerte",
    #   "source": "instagram",
    #   "original_item_details": {"post_id": "IG001", "caption": "...", "image_url": "url1"}
    # }
    # ... y así para los demás items.
