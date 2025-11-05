from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Product

class GenerateQRAPITestCase(APITestCase):
    def setUp(self):
        self.url = reverse('generate_qr_api')
        # создаём тестовые продукты
        self.product1 = Product.objects.create(
            name="34100030", barcode="8713968316602", created_at="2024-01-01",
            group="Test", show_on_site=True, external_id="85053"
        )
        self.product2 = Product.objects.create(
            name="34100031", barcode="8713968316619", created_at="2024-01-01",
            group="Test", show_on_site=True, external_id="85063"
        )

    def test_generate_qr_for_selected_products(self):
        payload = {
            "product_ids": [self.product1.id, self.product2.id],
            "select_all": False,
            "include_barcode": True,
            "domain": ""
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["generated"], 2)
        self.assertTrue(data["success"])

    def test_generate_qr_missing_domain(self):
        payload = {
            "product_ids": [self.product1.id],
            "select_all": False,
            "include_barcode": True
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_generate_qr_nothing_selected(self):
        payload = {
            "product_ids": [],
            "select_all": False,
            "include_barcode": False,
            "domain": ""
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, 400)
