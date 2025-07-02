from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

# La lista de productos del marketplace se pasará como un argumento más a la herramienta,
# o la herramienta la accederá desde un contexto/estado si se diseña así.
# Por ahora, para que sea una herramienta autocontenida que el MasterAgent pueda invocar
# con todos sus datos necesarios, es mejor pasar marketplace_products.

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
    Busca productos en la lista de productos del marketplace según varios criterios.
    """
    if not marketplace_products:
        return []

    results = []
    for product in marketplace_products:
        match = True

        # Filtro por query (nombre o descripción)
        if query:
            query_lower = query.lower()
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
            if product.get('price', float('-inf')) < min_price:
                match = False

        # Filtro por precio máximo
        if max_price is not None and match:
            if product.get('price', float('inf')) > max_price:
                match = False

        # Filtro por rating mínimo
        if min_rating is not None and match:
            if product.get('ratings', {}).get('average_rating', float('-inf')) < min_rating:
                match = False

        # Filtro por disponibilidad (stock)
        if in_stock is not None and match:
            product_in_stock = product.get('stock', 0) > 0
            if product_in_stock != in_stock:
                match = False

        if match:
            results.append(product)

    return results

def search_products_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nodo del grafo para buscar productos basado en search_criteria.
    """
    print("---BUSCANDO PRODUCTOS---")
    criteria = state.get('search_criteria')
    marketplace_products = state.get('marketplace_products')

    if not criteria:
        print("No se proporcionaron criterios de búsqueda.")
        state['search_results'] = []
        return state

    if not marketplace_products:
        print("No hay productos del marketplace cargados para buscar.")
        state['search_results'] = []
        return state

    print(f"Criterios de búsqueda: {criteria}")

    results = search_products_in_marketplace(
        marketplace_products=marketplace_products,
        query=criteria.get('query'),
        category=criteria.get('category'),
        brand=criteria.get('brand'),
        min_price=criteria.get('min_price'),
        max_price=criteria.get('max_price'),
        min_rating=criteria.get('min_rating'),
        in_stock=criteria.get('in_stock')
    )

    # marketplace_products es ahora un argumento requerido.
    # El nodo search_products_node ya no es necesario aquí,
    # la herramienta será llamada directamente.


if __name__ == '__main__':
    # Ejemplo de uso directo de la función de búsqueda (ahora @tool)
    mock_products_data = [
        {
            "id": "MP001", "name": "Smartphone Avanzado XZ100", "price": 799.99, "category": "Electrónica",
            "brand": "TechGlobal", "stock": 10, "ratings": {"average_rating": 4.8},
            "description": "Un smartphone genial", "tags": ["móvil", "celular"]
        },
        {
            "id": "MP002", "name": "Auriculares ProSound", "price": 149.50, "category": "Electrónica",
            "brand": "AudioMax", "stock": 0, "ratings": {"average_rating": 4.6},
            "description": "Sonido increíble", "tags": ["audio"]
        },
        {
            "id": "MP003", "name": "Cafetera Espresso Automática", "price": 299.00, "category": "Hogar",
            "brand": "HomeBeans", "stock": 5, "ratings": {"average_rating": 4.9},
            "description": "Café perfecto", "tags": ["cocina"]
        },
        {
            "id": "MP004", "name": "Smart TV LED 55 pulgadas", "price": 499.00, "category": "Electrónica",
            "brand": "VisionPlus", "stock": 15, "ratings": {"average_rating": 4.5},
            "description": "Imágenes vibrantes", "tags": ["tv", "televisor"]
        }
    ]

    print("Búsqueda 1: 'smartphone'")
    res1 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "query": "smartphone"
    })
    for r in res1: print(f"  - {r['name']}")

    print("\nBúsqueda 2: categoría 'Hogar', max_price 300")
    res2 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "category": "Hogar",
        "max_price": 300
    })
    for r in res2: print(f"  - {r['name']}")

    print("\nBúsqueda 3: marca 'AudioMax', in_stock True")
    res3 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "brand": "AudioMax",
        "in_stock": True
    })
    for r in res3: print(f"  - {r['name']}") # No debería encontrar nada

    print("\nBúsqueda 4: min_rating 4.7")
    res4 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "min_rating": 4.7
    })
    for r in res4: print(f"  - {r['name']}")

    print("\nBúsqueda 5: query 'tv', in_stock True")
    res5 = catalog_search_tool.invoke({
        "marketplace_products": mock_products_data,
        "query": "tv",
        "in_stock": True
    })
    for r in res5: print(f"  - {r['name']}")
