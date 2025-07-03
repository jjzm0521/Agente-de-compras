import json
import os # Importado para el bloque if __name__ == '__main__'
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.utils.config import get_llm
from src.utils.data_loader import get_instagram_saves, get_pinterest_boards # Para carga de datos si es necesario

# --- Pydantic Modelos para la Salida Estructurada del LLM ---

class CategorizedItem(BaseModel):
    """
    Representa un item de una red social (Instagram post, Pinterest pin)
    analizado y categorizado por el LLM.
    Esta estructura es la que se espera que el LLM devuelva.
    """
    original_text: str = Field(description="El texto original del post o pin que fue analizado.")
    identified_product_name: Optional[str] = Field(
        description="El nombre del producto o servicio identificado en el texto. Si no se identifica un producto claro, puede ser una descripción breve del objeto de deseo."
    )
    category: Optional[str] = Field(
        description="Categoría estimada para el producto/servicio (ej: Electrónica, Ropa, Hogar, Viajes, Comida, Libros, Belleza, Deporte, Otro)."
    )
    key_features: List[str] = Field(
        description="Una lista de características clave, palabras clave o atributos mencionados sobre el producto/servicio."
    )
    user_sentiment_or_intent: Optional[str] = Field(
        description="Sentimiento o intención del usuario hacia el item (ej: deseo fuerte, consideración, necesita oferta, inspiración)."
    )
    source: str = Field(description="La fuente original del item desde donde se extrajo (ej: 'instagram', 'pinterest').")
    original_item_details: Dict[Any, Any] = Field(
        description="Detalles completos del item original tal como se obtuvieron de la fuente (ej: el JSON completo del post de Instagram)."
    )

class WishlistAnalysisResult(BaseModel):
    """
    Contenedor para la lista de todos los items analizados por el WishlistAgent.
    Aunque no se usa directamente como salida del LLM por item, podría usarse si el LLM analizara un batch.
    Actualmente, el estado del agente (`ia_categorized_wishlist`) contendrá una lista de `CategorizedItem` (como dicts).
    """
    categorized_items: List[CategorizedItem] = Field(description="Lista de items de wishlist analizados y categorizados por el LLM.")


# --- Plantilla de Prompt para el Análisis de Items de Wishlist ---
# Esta plantilla instruye al LLM sobre cómo analizar cada item de la wishlist.
WISHLIST_ANALYSIS_PROMPT_TEMPLATE = """
Eres un asistente experto en analizar listas de deseos de redes sociales.
Tu tarea es analizar el siguiente item de una lista de deseos (proveniente de {source}) y extraer información relevante.

Texto del item a analizar:
---
{text_input}
---

Contexto adicional del item original (solo para tu referencia, no lo incluyas directamente en la respuesta a menos que sea parte del análisis y lo cites explícitamente):
{original_details_str}

---
Instrucciones de Extracción:
Por favor, extrae la siguiente información del "Texto del item a analizar" y formatea tu respuesta como un objeto JSON que se ajuste al esquema de `CategorizedItem`.
Asegúrate de que todos los campos requeridos por `CategorizedItem` estén presentes en tu respuesta JSON.

Campos a rellenar en el JSON:
-   `original_text`: (str) DEBE ser exactamente el mismo "Texto del item a analizar" proporcionado arriba.
-   `identified_product_name`: (Optional[str]) El nombre del producto o servicio específico que el usuario parece desear. Si no es un producto claro, describe brevemente el objeto de deseo (ej: "un viaje a la playa", "auriculares con cancelación de ruido"). Si no se puede identificar, usa `null`.
-   `category`: (Optional[str]) La categoría más apropiada para este producto/servicio. Elige UNA de la siguiente lista: Electrónica, Ropa, Hogar, Viajes, Comida, Libros, Belleza, Deporte, Otro. Si no aplica o no se puede determinar, usa `null`.
-   `key_features`: (List[str]) Una lista de 2 a 4 características clave, palabras clave, marcas o atributos mencionados directamente en el texto sobre el producto/servicio. Si no hay características claras, puede ser una lista vacía `[]`.
-   `user_sentiment_or_intent`: (Optional[str]) Describe brevemente el sentimiento o la intención principal del usuario hacia el item, inferido del texto (ej: "deseo fuerte", "consideración casual", "buscando oferta", "inspiración general", "necesidad específica"). Si no se puede determinar, usa `null`.
-   `source`: (str) DEBE ser el valor de `{source}` proporcionado (ej: "instagram" o "pinterest").
-   `original_item_details`: (Dict[Any, Any]) DEBE ser una copia EXACTA del JSON proporcionado en "Contexto adicional del item original".

---
Formato de Salida Obligatorio:
Responde ÚNICAMENTE con el objeto JSON que se adhiere al esquema de `CategorizedItem` y las instrucciones anteriores. No incluyas explicaciones adicionales, comentarios ni texto introductorio fuera del JSON.

Ejemplo de cómo se vería el JSON de respuesta (sin las comillas triples externas y asumiendo que los datos de entrada coinciden):
```json
{{
  "original_text": "¡Me encantan estos nuevos auriculares! #AudioMax #ProSound #GadgetGoals",
  "identified_product_name": "Auriculares ProSound de AudioMax",
  "category": "Electrónica",
  "key_features": ["auriculares", "ProSound", "AudioMax", "GadgetGoals"],
  "user_sentiment_or_intent": "deseo fuerte",
  "source": "instagram",
  "original_item_details": {{ "post_id": "INSTA_POST_001", "user": "user123", "caption": "¡Me encantan estos nuevos auriculares! #AudioMax #ProSound #GadgetGoals", "image_url": "http://example.com/img.jpg" }}
}}
```
"""

# --- Funciones del Agente ---

def analyze_social_media_item(
    llm: Any, # Tipo genérico para el objeto LLM de Langchain
    item_text: str,
    source: str,
    original_item_data: Dict
) -> Optional[CategorizedItem]:
    """
    Analiza un solo item de red social (Instagram post o Pinterest pin) utilizando un LLM
    para extraer información estructurada y categorizarla.

    Args:
        llm: La instancia del modelo de lenguaje de Langchain a utilizar.
        item_text: El texto principal del item a analizar (ej: caption de Instagram, descripción de Pinterest).
        source: La plataforma de origen del item (ej: "instagram", "pinterest").
        original_item_data: El diccionario completo con los datos originales del item,
                            tal como se cargaron desde la fuente.

    Returns:
        Un objeto `CategorizedItem` con la información analizada si el proceso es exitoso,
        o `None` si ocurre un error durante el análisis o la respuesta del LLM no es válida.
    """
    prompt = ChatPromptTemplate.from_template(WISHLIST_ANALYSIS_PROMPT_TEMPLATE)

    # Crear una cadena LangChain. Se usa `.with_structured_output(CategorizedItem)`
    # para que Langchain automáticamente intente parsear la salida JSON del LLM
    # al modelo Pydantic `CategorizedItem`.
    chain = prompt | llm.with_structured_output(CategorizedItem)

    try:
        # Invocar la cadena con los datos del item.
        # El LLM debe generar todos los campos de CategorizedItem según el prompt.
        response_item: CategorizedItem = chain.invoke({
            "source": source,
            "text_input": item_text,
            "original_details_str": json.dumps(original_item_data, indent=2, ensure_ascii=False) # Para el contexto del LLM
        })

        # Verificación adicional (aunque el prompt es explícito):
        # Asegurarse de que los campos que pasamos directamente (source, original_text, original_item_details)
        # coincidan o sean correctamente establecidos por el LLM según el prompt.
        # Si el LLM no los llena como se espera, se podrían sobrescribir aquí, pero es mejor
        # que el prompt sea lo suficientemente robusto.
        # response_item.original_text = item_text # El prompt le pide al LLM que lo haga.
        # response_item.source = source # El prompt le pide al LLM que lo haga.
        # response_item.original_item_details = original_item_data # El prompt le pide al LLM que lo haga.

        return response_item
    except Exception as e:
        print(f"Error analizando item '{item_text[:50]}...' de '{source}' con LLM: {e}")
        # Podríamos intentar parsear el error si es una OutputParsingError para ver la salida del LLM.
        return None

def run_wishlist_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del grafo LangGraph para el WishlistAgent.
    Este agente toma los datos cargados de Instagram y Pinterest (desde el `state`),
    los analiza utilizando un LLM para extraer información de productos y categorizarlos,
    y luego actualiza el `state` con la lista de items analizados en `ia_categorized_wishlist`.

    Args:
        state: El diccionario de estado actual del grafo del agente. Se espera que contenga
               `instagram_saves` y `pinterest_boards` con los datos cargados.

    Returns:
        El diccionario de estado actualizado. Si el análisis es exitoso, `ia_categorized_wishlist`
        contendrá una lista de diccionarios (cada uno un `CategorizedItem`).
        Si hay un error (ej: API key no configurada), `wishlist_agent_error` se poblará.
    """
    print("--- EJECUTANDO WISHLIST AGENT (Análisis y Categorización con IA) ---")

    # Obtener la instancia del LLM.
    # Se usa una temperatura baja para que las respuestas del LLM sean más consistentes y deterministas.
    try:
        llm = get_llm(temperature=0.1)
    except ValueError as e:
        # Error crítico si el LLM no se puede inicializar (ej: API key no configurada).
        print(f"ERROR CRÍTICO: No se pudo inicializar el LLM para WishlistAgent: {e}")
        print("El WishlistAgent no puede continuar sin un LLM configurado. Revise la configuración de la API Key.")
        state['ia_categorized_wishlist'] = [] # Dejar la lista vacía
        state['wishlist_agent_error'] = f"Fallo al inicializar LLM: {e}"
        return state

    # Obtener datos de las redes sociales del estado del agente.
    # Estos datos deberían haber sido cargados en un paso anterior (ej: en main.py o un nodo de carga).
    instagram_data = state.get('instagram_saves')
    pinterest_data = state.get('pinterest_boards')

    # Como fallback, si los datos no están en el estado, intentar cargarlos.
    # En un flujo de producción, la carga de datos sería manejada más estrictamente.
    if not instagram_data:
        print("WARN: Datos de Instagram no encontrados en el estado. Intentando cargar...")
        instagram_data = get_instagram_saves()
        state['instagram_saves'] = instagram_data # Actualizar estado si se cargó aquí

    if not pinterest_data:
        print("WARN: Datos de Pinterest no encontrados en el estado. Intentando cargar...")
        pinterest_data = get_pinterest_boards()
        state['pinterest_boards'] = pinterest_data # Actualizar estado si se cargó aquí

    analyzed_items_list: List[CategorizedItem] = [] # Lista para guardar los objetos CategorizedItem

    # Analizar Items Guardados de Instagram
    if instagram_data and isinstance(instagram_data.get('saved_items'), list):
        print(f"Analizando {len(instagram_data['saved_items'])} items de Instagram...")
        for item in instagram_data['saved_items']:
            text_to_analyze = item.get('caption', '')
            if not text_to_analyze.strip(): # Saltar si no hay texto en el caption
                print(f"Skipping Instagram item ID {item.get('post_id', 'N/A')} due to empty caption.")
                continue

            # Analizar el item usando el LLM
            categorized_item_obj = analyze_social_media_item(llm, text_to_analyze, "instagram", item)
            if categorized_item_obj:
                analyzed_items_list.append(categorized_item_obj)
    else:
        print("No hay datos válidos de Instagram ('saved_items' no es una lista o no existe) para analizar.")

    # Analizar Pines de Pinterest
    if pinterest_data and isinstance(pinterest_data.get('boards'), list):
        print("Analizando items de Pinterest...")
        for board in pinterest_data['boards']:
            if isinstance(board.get('pins'), list):
                for pin in board['pins']:
                    text_to_analyze = pin.get('description', '')
                    if not text_to_analyze.strip(): # Saltar si no hay texto en la descripción
                        print(f"Skipping Pinterest pin ID {pin.get('pin_id', 'N/A')} due to empty description.")
                        continue

                    # Analizar el pin usando el LLM
                    categorized_item_obj = analyze_social_media_item(llm, text_to_analyze, "pinterest", pin)
                    if categorized_item_obj:
                        analyzed_items_list.append(categorized_item_obj)
            else:
                print(f"Skipping Pinterest board ID {board.get('board_id','N/A')} due to invalid 'pins' field.")
    else:
        print("No hay datos válidos de Pinterest ('boards' no es una lista o no existe) para analizar.")

    # TODO Futuro: Considerar si se deben analizar también los 'abandoned_carts' con IA.
    # Actualmente, los carritos abandonados suelen tener IDs de producto directos, por lo que
    # el matching puede ser más directo sin necesidad de análisis semántico profundo por LLM,
    # a menos que queramos inferir intenciones o razones de abandono (si tuviéramos más contexto).

    # Guardar los items analizados (como diccionarios) en el estado del agente.
    state['ia_categorized_wishlist'] = [item.model_dump() for item in analyzed_items_list]
    print(f"WishlistAgent: {len(analyzed_items_list)} items analizados y categorizados por IA en total.")

    # Limpiar cualquier error previo si el proceso se completó (aunque sea con 0 items analizados)
    if 'wishlist_agent_error' in state and not analyzed_items_list and not (instagram_data or pinterest_data):
        # Mantener el error si no había datos y no se pudo hacer nada.
        pass
    elif 'wishlist_agent_error' in state:
         del state['wishlist_agent_error']


    return state

# --- Bloque de Prueba (ejecutar con `python src/agent/wishlist_agent.py`) ---
if __name__ == '__main__':
    # Crear un estado simulado para probar el WishlistAgent.
    # Esto simula los datos que el agente esperaría encontrar en el `state` del grafo.
    mock_state_for_test = {
        "instagram_saves": {
            "user_id": "test_insta_user_123",
            "saved_items": [
                {"post_id": "IG001", "user": "insta_user_A", "caption": "Amo esta nueva laptop super rápida para gaming! Ideal para #tech y #trabajo. Marca X Modelo Y.", "image_url": "http://example.com/laptop.jpg", "likes": 120},
                {"post_id": "IG002", "user": "insta_user_B", "caption": "Qué bonitas zapatillas para correr. Las necesito para mi maratón. #run #fitness", "image_url": "http://example.com/shoes.jpg", "likes": 88},
                {"post_id": "IG003", "user": "insta_user_C", "caption": "Unas vacaciones en la playa de Cancún serían geniales ahora mismo... #viajes #sol #playa", "image_url": "http://example.com/beach.jpg", "likes": 250},
                {"post_id": "IG004", "user": "insta_user_D", "caption": "", "image_url": "http://example.com/empty.jpg", "likes": 10} # Item sin caption
            ]
        },
        "pinterest_boards": {
            "user_id": "test_pin_user_456",
            "boards": [{
                "board_id": "B01", "board_name": "Gadgets y Tecnología",
                "pins": [
                    {"pin_id": "P001", "board_name": "Gadgets y Tecnología", "description": "El mejor smartwatch para monitorear salud y ejercicio diario. Compatible con iOS y Android.", "link": "http://example.com/smartwatch", "image_url": "http://example.com/watch.jpg"},
                    {"pin_id": "P002", "board_name": "Gadgets y Tecnología", "description": "Ideas para decorar la sala con un estilo minimalista y moderno. #decor #hogar", "link": "http://example.com/decor", "image_url": "http://example.com/livingroom.jpg"}
                ]
            }, {
                "board_id": "B02", "board_name": "Recetas Deliciosas",
                "pins": [
                     {"pin_id": "P003", "board_name": "Recetas Deliciosas", "description": "Pastel de chocolate fácil y rápido.", "link": "http://example.com/cake", "image_url": "http://example.com/chocolatecake.jpg"}
                ]
            }]
        }
        # Para probar el WishlistAgent sin una API key válida (y evitar costos o errores si no está configurada),
        # se necesitaría mockear `get_llm` para que devuelva un LLM falso o uno que no haga llamadas reales.
        # Por ahora, esta prueba intentará usar el LLM real si la API key está en .env.
    }
    print("--- INICIANDO PRUEBA DEL WISHLIST AGENT ---")
    print("(Requiere API Key de OpenAI configurada en .env para un análisis completo con LLM)")

    # Ajustar el path para asegurar que .env se cargue desde la raíz del proyecto
    # si el script se ejecuta directamente desde `src/agent/`.
    if os.path.basename(os.getcwd()) == "agent": # Estamos en src/agent/
        project_root = os.path.join("..", "..")
        os.chdir(project_root)
        print(f"Cambiado directorio a la raíz del proyecto: {os.getcwd()} para cargar .env correctamente.")
    elif os.path.basename(os.getcwd()) == "src": # Estamos en src/
        project_root = ".."
        os.chdir(project_root)
        print(f"Cambiado directorio a la raíz del proyecto: {os.getcwd()} para cargar .env correctamente.")

    # Ejecutar el agente con el estado simulado
    final_state = run_wishlist_agent(mock_state_for_test)

    print("\n--- ESTADO FINAL DESPUÉS DE EJECUTAR WishlistAgent ---")
    if final_state.get('wishlist_agent_error'):
        print(f"ERROR reportado por WishlistAgent: {final_state['wishlist_agent_error']}")

    print("\nWishlist Analizada y Categorizada por IA (`ia_categorized_wishlist`):")
    if final_state.get('ia_categorized_wishlist'):
        for i, item_data in enumerate(final_state['ia_categorized_wishlist']):
            print(f"\nItem Analizado #{i+1}:")
            # Convertir el diccionario de nuevo a un objeto Pydantic para una impresión más bonita o validación
            try:
                item_model = CategorizedItem(**item_data)
                # Usar model_dump_json para una salida JSON formateada.
                print(item_model.model_dump_json(indent=2, exclude_none=True)) # exclude_none para no mostrar campos nulos
            except Exception as pydantic_error:
                print(f"Error al parsear item_data a CategorizedItem: {pydantic_error}")
                print(f"Datos crudos del item: {item_data}")
    else:
        print("No se generó ninguna wishlist categorizada por IA (o la lista está vacía).")

    print("\n--- FIN DE PRUEBA DEL WISHLIST AGENT ---")

    # Ejemplo de cómo se vería la salida JSON para un item si el LLM funciona correctamente:
    # (Esto es solo una simulación del formato esperado, el contenido real del LLM puede variar)
    # {
    #   "original_text": "Amo esta nueva laptop super rápida para gaming! Ideal para #tech y #trabajo. Marca X Modelo Y.",
    #   "identified_product_name": "Laptop para gaming Marca X Modelo Y",
    #   "category": "Electrónica",
    #   "key_features": ["rápida", "gaming", "tech", "trabajo", "Marca X Modelo Y"],
    #   "user_sentiment_or_intent": "deseo fuerte",
    #   "source": "instagram",
    #   "original_item_details": {
    #     "post_id": "IG001",
    #     "user": "insta_user_A",
    #     "caption": "Amo esta nueva laptop super rápida para gaming! Ideal para #tech y #trabajo. Marca X Modelo Y.",
    #     "image_url": "http://example.com/laptop.jpg",
    #     "likes": 120
    #   }
    # }
    # ... y así para los demás items que tengan texto y sean procesados.
