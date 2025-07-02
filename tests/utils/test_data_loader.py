import unittest
import json
import os
from src.utils import data_loader

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # Crear archivos JSON de prueba temporales
        self.test_data_dir = "test_temp_data"
        os.makedirs(self.test_data_dir, exist_ok=True)

        self.products_file = os.path.join(self.test_data_dir, "products.json")
        self.insta_file = os.path.join(self.test_data_dir, "insta.json")
        self.pinterest_file = os.path.join(self.test_data_dir, "pinterest.json")
        self.carts_file = os.path.join(self.test_data_dir, "carts.json")
        self.invalid_json_file = os.path.join(self.test_data_dir, "invalid.json")

        self.sample_products = [{"id": "P1", "name": "Product 1"}]
        self.sample_insta = {"user_id": "insta_user", "saved_items": [{"post_id": "I1"}]}
        self.sample_pinterest = {"user_id": "pin_user", "boards": [{"board_id": "B1"}]}
        self.sample_carts = [{"cart_id": "C1", "items": [{"product_id": "P1"}]}]

        with open(self.products_file, 'w') as f:
            json.dump(self.sample_products, f)
        with open(self.insta_file, 'w') as f:
            json.dump(self.sample_insta, f)
        with open(self.pinterest_file, 'w') as f:
            json.dump(self.sample_pinterest, f)
        with open(self.carts_file, 'w') as f:
            json.dump(self.sample_carts, f)
        with open(self.invalid_json_file, 'w') as f:
            f.write("{'invalid_json': True,}") # JSON inválido

    def tearDown(self):
        # Eliminar archivos y directorio temporales
        os.remove(self.products_file)
        os.remove(self.insta_file)
        os.remove(self.pinterest_file)
        os.remove(self.carts_file)
        os.remove(self.invalid_json_file)
        os.rmdir(self.test_data_dir)

    def test_load_json_data_success(self):
        data = data_loader.load_json_data(self.products_file)
        self.assertEqual(data, self.sample_products)

    def test_load_json_data_file_not_found(self):
        data = data_loader.load_json_data("non_existent_file.json")
        self.assertIsNone(data)

    def test_load_json_data_invalid_json(self):
        data = data_loader.load_json_data(self.invalid_json_file)
        self.assertIsNone(data)

    def test_get_marketplace_products(self):
        products = data_loader.get_marketplace_products(data_path=self.products_file)
        self.assertEqual(products, self.sample_products)

    def test_get_instagram_saves(self):
        insta_saves = data_loader.get_instagram_saves(data_path=self.insta_file)
        self.assertEqual(insta_saves, self.sample_insta)

    def test_get_pinterest_boards(self):
        pinterest_boards = data_loader.get_pinterest_boards(data_path=self.pinterest_file)
        self.assertEqual(pinterest_boards, self.sample_pinterest)

    def test_get_abandoned_carts(self):
        carts = data_loader.get_abandoned_carts(data_path=self.carts_file)
        self.assertEqual(carts, self.sample_carts)

if __name__ == '__main__':
    unittest.main()
