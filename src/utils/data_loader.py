import json
from typing import List, Dict, Any, Optional

def load_json_data(file_path: str) -> Any:
    """
    Carga datos desde un archivo JSON.

    Args:
        file_path: Ruta al archivo JSON.

    Returns:
        Datos cargados desde el archivo JSON.
        Retorna None si el archivo no se encuentra o hay un error de decodificación.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: No se pudo decodificar el JSON en {file_path}")
        return None

def get_marketplace_products(data_path: str = "data/marketplace_products.json") -> Optional[List[Dict[str, Any]]]:
    """Carga los productos del marketplace."""
    return load_json_data(data_path)

def get_instagram_saves(data_path: str = "data/instagram_saves.json") -> Optional[Dict[str, Any]]:
    """Carga los elementos guardados de Instagram."""
    return load_json_data(data_path)

def get_pinterest_boards(data_path: str = "data/pinterest_boards.json") -> Optional[Dict[str, Any]]:
    """Carga los tableros y pines de Pinterest."""
    return load_json_data(data_path)

def get_abandoned_carts(data_path: str = "data/abandoned_carts.json") -> Optional[List[Dict[str, Any]]]:
    """Carga los carritos abandonados."""
    return load_json_data(data_path)

if __name__ == '__main__':
    # Ejemplo de uso
    products = get_marketplace_products()
    if products:
        print(f"Cargados {len(products)} productos del marketplace.")
        # print(products[0])

    insta_saves = get_instagram_saves()
    if insta_saves:
        print(f"Cargados {len(insta_saves.get('saved_items', []))} elementos guardados de Instagram para el usuario {insta_saves.get('user_id')}.")
        # if insta_saves.get('saved_items'):
        #     print(insta_saves['saved_items'][0])

    pinterest_data = get_pinterest_boards()
    if pinterest_data:
        print(f"Cargados {len(pinterest_data.get('boards', []))} tableros de Pinterest para el usuario {pinterest_data.get('user_id')}.")
        # if pinterest_data.get('boards'):
        #     print(pinterest_data['boards'][0]['pins'][0])

    carts = get_abandoned_carts()
    if carts:
        print(f"Cargados {len(carts)} carritos abandonados.")
        # print(carts[0])
