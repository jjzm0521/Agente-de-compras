from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

# El decorador `@tool` de Langchain convierte esta función en una herramienta
# que puede ser utilizada por agentes de Langchain.
# La documentación (docstring) de la función es importante, ya que Langchain
# puede usarla para entender cómo y cuándo utilizar la herramienta.

@tool
def catalog_search_tool(
    marketplace_products: List[Dict[str, Any]],
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Busca productos en la lista de productos del marketplace (`marketplace_products`)
    según varios criterios de filtrado.

    Args:
        marketplace_products: Una lista de diccionarios, donde cada diccionario representa un producto.
                              Se espera que este argumento sea proporcionado por el sistema del agente,
                              generalmente cargado desde el estado del agente.
        query: Texto a buscar en el nombre, descripción o etiquetas del producto (case-insensitive).
        category: Categoría específica del producto a filtrar (case-insensitive).
        brand: Marca específica del producto a filtrar (case-insensitive).
        min_price: Precio mínimo del producto.
        max_price: Precio máximo del producto.
        min_rating: Rating promedio mínimo del producto.
        in_stock: Filtrar por disponibilidad (True para en stock, False para fuera de stock).

    Returns:
        Una lista de diccionarios de productos que coinciden con todos los criterios proporcionados.
        Retorna una lista vacía si no se encuentran productos o si `marketplace_products` está vacío.
        En caso de error interno (poco probable con esta lógica), podría retornar una lista vacía.
    """
    if not marketplace_products:
        # Si no hay productos en el catálogo, no hay nada que buscar.
        return []

    results = []
    for product in marketplace_products:
        # Asumimos que el producto coincide hasta que un criterio falle
        match = True

        # Filtro por query (búsqueda de texto en nombre, descripción o etiquetas)
        if query:
            query_lower = query.lower()
            # El producto debe contener la query en alguno de sus campos de texto relevantes.
            if not (query_lower in product.get('name', '').lower() or \
                    query_lower in product.get('description', '').lower() or \
                    any(query_lower in tag.lower() for tag in product.get('tags', []))):
                match = False

        # Filtro por categoría
        if category and match:
            if product.get('category', '').lower() != category.lower():
                match = False

        # Filtro por marca
        if brand and match:
            if product.get('brand', '').lower() != brand.lower():
                match = False

        # Filtro por precio mínimo
        if min_price is not None and match:
            # Usamos float('-inf') como default si el precio no existe para asegurar que la comparación funcione.
            if product.get('price', float('-inf')) < min_price:
                match = False

        # Filtro por precio máximo
        if max_price is not None and match:
            # Usamos float('inf') como default si el precio no existe.
            if product.get('price', float('inf')) > max_price:
                match = False

        # Filtro por rating mínimo
        if min_rating is not None and match:
            # Accedemos al rating promedio, usando float('-inf') como default.
            if product.get('ratings', {}).get('average_rating', float('-inf')) < min_rating:
                match = False

        # Filtro por disponibilidad (stock)
        if in_stock is not None and match:
            # Consideramos que un producto está en stock si su cantidad es mayor a 0.
            product_in_stock = product.get('stock', 0) > 0
            if product_in_stock != in_stock:
                match = False

        # Si todos los criterios aplicados hasta ahora son verdaderos, el producto es un resultado.
        if match:
            results.append(product)

    return results

# La función `search_products_node` que existía antes aquí ya no es necesaria
# porque el `catalog_search_tool` está diseñado para ser llamado directamente
# por el `MasterAgent` a través del mecanismo de herramientas de LangGraph.
# El nodo del grafo que ejecuta la herramienta se encargará de pasar `marketplace_products`
# desde el estado del agente.

# --- Bloque de Prueba (ejecutar con `python src/agent/search_handler.py`) ---
if __name__ == '__main__':
    # Datos de ejemplo para probar la herramienta de búsqueda.
    # Estos simulan la estructura de `marketplace_products.json`.
    mock_products_data = [
        {
            "id": "MP001", "name": "Smartphone Avanzado XZ100", "price": 799.99, "currency": "USD",
            "category": "Electrónica", "brand": "TechGlobal", "stock": 10,
            "ratings": {"average_rating": 4.8, "count": 150},
            "description": "Un smartphone genial con la última tecnología y cámara de alta resolución.",
            "tags": ["móvil", "celular", "smartphone", "tecnología"]
        },
        {
            "id": "MP002", "name": "Auriculares ProSound", "price": 149.50, "currency": "USD",
            "category": "Electrónica", "brand": "AudioMax", "stock": 0, # Fuera de stock
            "ratings": {"average_rating": 4.6, "count": 210},
            "description": "Sonido increíble con cancelación de ruido y batería de larga duración.",
            "tags": ["audio", "auriculares", "música", "cancelación de ruido"]
        },
        {
            "id": "MP003", "name": "Cafetera Espresso Automática", "price": 299.00, "currency": "USD",
            "category": "Hogar", "brand": "HomeBeans", "stock": 5,
            "ratings": {"average_rating": 4.9, "count": 90},
            "description": "Café perfecto cada mañana con solo presionar un botón. Múltiples programas.",
            "tags": ["cocina", "café", "espresso", "electrodoméstico"]
        },
        {
            "id": "MP004", "name": "Smart TV LED 55 pulgadas 4K", "price": 499.00, "currency": "USD",
            "category": "Electrónica", "brand": "VisionPlus", "stock": 15,
            "ratings": {"average_rating": 4.5, "count": 320},
            "description": "Imágenes vibrantes y realistas con resolución 4K Ultra HD. Acceso a apps.",
            "tags": ["tv", "televisor", "smart tv", "4k", "entretenimiento"]
        },
        {
            "id": "MP005", "name": "Zapatillas Deportivas RunnerX", "price": 89.99, "currency": "USD",
            "category": "Deporte", "brand": "FitStep", "stock": 25,
            "ratings": {"average_rating": 4.3, "count": 120},
            "description": "Comodidad y rendimiento para tus carreras diarias. Materiales ligeros.",
            "tags": ["calzado", "running", "deporte", "zapatillas"]
        }
    ]

    print("--- PRUEBAS DE catalog_search_tool ---")

    print("\nBúsqueda 1: Query 'smartphone'")
    # La herramienta se invoca con un diccionario que contiene todos sus argumentos.
    # `marketplace_products` es el primer argumento posicional o nombrado.
    res1 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "query": "smartphone"
    })
    print(f"  Resultados ({len(res1)}):")
    for r in res1: print(f"    - {r['name']} (ID: {r['id']})")

    print("\nBúsqueda 2: Categoría 'Hogar', Precio Máximo 300")
    res2 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "category": "Hogar",
        "max_price": 300.00 # Es buena práctica usar el mismo tipo (float)
    })
    print(f"  Resultados ({len(res2)}):")
    for r in res2: print(f"    - {r['name']} (Precio: {r['price']})")

    print("\nBúsqueda 3: Marca 'AudioMax', En Stock: True")
    res3 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "brand": "AudioMax",
        "in_stock": True # Producto MP002 de AudioMax está fuera de stock
    })
    print(f"  Resultados ({len(res3)}):") # Debería ser 0
    if not res3: print("    - No se encontraron productos (esperado).")
    for r in res3: print(f"    - {r['name']}")

    print("\nBúsqueda 4: Rating Mínimo 4.7")
    res4 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "min_rating": 4.7
    })
    print(f"  Resultados ({len(res4)}):")
    for r in res4: print(f"    - {r['name']} (Rating: {r['ratings']['average_rating']})")

    print("\nBúsqueda 5: Query 'tv', En Stock: True, Marca 'VisionPlus'")
    res5 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "query": "tv",
        "in_stock": True,
        "brand": "VisionPlus"
    })
    print(f"  Resultados ({len(res5)}):")
    for r in res5: print(f"    - {r['name']}")

    print("\nBúsqueda 6: Sin criterios (debería devolver todos los productos)")
    res6 = catalog_search_tool.invoke({"marketplace_products": mock_products_data})
    print(f"  Resultados ({len(res6)}):")
    # for r in res6: print(f"    - {r['name']}") # Comentado para no alargar mucho la salida
    if len(res6) == len(mock_products_data):
        print(f"    - Se devolvieron todos los {len(mock_products_data)} productos (esperado).")
    else:
        print(f"    - ERROR: Se esperaban {len(mock_products_data)} productos, se obtuvieron {len(res6)}.")

    print("\nBúsqueda 7: Catálogo vacío")
    res7 = catalog_search_tool.invoke({"marketplace_products": []})
    print(f"  Resultados ({len(res7)}):")
    if not res7: print("    - No se encontraron productos (esperado).")

    print("\n--- FIN DE PRUEBAS ---")
