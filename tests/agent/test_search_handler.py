import unittest
from src.agent.search_handler import search_products_in_marketplace

class TestSearchHandler(unittest.TestCase):

    def setUp(self):
        self.mock_products = [
            {
                "id": "MP001", "name": "Smartphone Avanzado XZ100", "price": 799.99,
                "category": "Electrónica", "brand": "TechGlobal", "stock": 10,
                "ratings": {"average_rating": 4.8}, "description": "Un smartphone genial", "tags": ["móvil", "celular"]
            },
            {
                "id": "MP002", "name": "Auriculares ProSound", "price": 149.50,
                "category": "Electrónica", "brand": "AudioMax", "stock": 0,
                "ratings": {"average_rating": 4.6}, "description": "Sonido increíble", "tags": ["audio"]
            },
            {
                "id": "MP003", "name": "Cafetera Espresso Automática", "price": 299.00,
                "category": "Hogar", "brand": "HomeBeans", "stock": 5,
                "ratings": {"average_rating": 4.9}, "description": "Café perfecto", "tags": ["cocina"]
            },
            {
                "id": "MP004", "name": "Smart TV LED 55 pulgadas", "price": 499.00,
                "category": "Electrónica", "brand": "VisionPlus", "stock": 15,
                "ratings": {"average_rating": 4.5}, "description": "Imágenes vibrantes", "tags": ["tv", "televisor"]
            },
            {
                "id": "MP005", "name": "Libro de Cocina Saludable", "price": 29.99,
                "category": "Libros", "brand": "Editorial Gourmet", "stock": 50,
                "ratings": {"average_rating": 4.2}, "description": "Recetas fáciles y nutritivas", "tags": ["cocina", "recetas"]
            }
        ]

    def test_search_no_criteria(self):
        results = search_products_in_marketplace(self.mock_products)
        self.assertEqual(len(results), 5) # Devuelve todos los productos

    def test_search_by_query_name(self):
        results = search_products_in_marketplace(self.mock_products, query="Smartphone")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP001")

    def test_search_by_query_description(self):
        results = search_products_in_marketplace(self.mock_products, query="Sonido increíble")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP002")

    def test_search_by_query_tags(self):
        results = search_products_in_marketplace(self.mock_products, query="cocina")
        self.assertEqual(len(results), 2) # Cafetera y Libro de Cocina
        ids = {r['id'] for r in results}
        self.assertIn("MP003", ids)
        self.assertIn("MP005", ids)

    def test_search_by_category(self):
        results = search_products_in_marketplace(self.mock_products, category="Hogar")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP003")

    def test_search_by_brand(self):
        results = search_products_in_marketplace(self.mock_products, brand="TechGlobal")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP001")

    def test_search_by_min_price(self):
        results = search_products_in_marketplace(self.mock_products, min_price=300.00)
        self.assertEqual(len(results), 2) # Smartphone y Smart TV
        ids = {r['id'] for r in results}
        self.assertIn("MP001", ids)
        self.assertIn("MP004", ids)

    def test_search_by_max_price(self):
        results = search_products_in_marketplace(self.mock_products, max_price=150.00)
        self.assertEqual(len(results), 2) # Auriculares y Libro
        ids = {r['id'] for r in results}
        self.assertIn("MP002", ids)
        self.assertIn("MP005", ids)

    def test_search_by_price_range(self):
        results = search_products_in_marketplace(self.mock_products, min_price=100.00, max_price=500.00)
        self.assertEqual(len(results), 3) # Auriculares, Cafetera, Smart TV
        ids = {r['id'] for r in results}
        self.assertIn("MP002", ids)
        self.assertIn("MP003", ids)
        self.assertIn("MP004", ids)

    def test_search_by_min_rating(self):
        results = search_products_in_marketplace(self.mock_products, min_rating=4.7)
        self.assertEqual(len(results), 2) # Smartphone y Cafetera
        ids = {r['id'] for r in results}
        self.assertIn("MP001", ids)
        self.assertIn("MP003", ids)

    def test_search_by_in_stock_true(self):
        results = search_products_in_marketplace(self.mock_products, in_stock=True)
        self.assertEqual(len(results), 4) # Todos menos los auriculares
        ids = {r['id'] for r in results}
        self.assertNotIn("MP002", ids)

    def test_search_by_in_stock_false(self):
        results = search_products_in_marketplace(self.mock_products, in_stock=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP002") # Solo los auriculares

    def test_search_combined_criteria(self):
        # Electrónica, en stock, precio < 500
        results = search_products_in_marketplace(self.mock_products, category="Electrónica", in_stock=True, max_price=500.00)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], "MP004") # Smart TV

    def test_search_no_results(self):
        results = search_products_in_marketplace(self.mock_products, query="inexistente", brand="NoBrand")
        self.assertEqual(len(results), 0)

    def test_search_empty_product_list(self):
        results = search_products_in_marketplace([], query="smartphone")
        self.assertEqual(len(results), 0)

    def test_search_product_without_optional_fields(self):
        product_sin_campos = [{"id": "P_SIN", "name": "Producto Pelado"}] # Sin precio, categoria, etc.
        results_query = search_products_in_marketplace(product_sin_campos, query="Pelado")
        self.assertEqual(len(results_query), 1)

        results_price = search_products_in_marketplace(product_sin_campos, max_price=100)
        self.assertEqual(len(results_price), 0) # No debería fallar, pero no machea

        results_stock = search_products_in_marketplace(product_sin_campos, in_stock=True)
        self.assertEqual(len(results_stock), 0) # No debería fallar, pero no machea (stock 0 por defecto)


if __name__ == '__main__':
    unittest.main()
