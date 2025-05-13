from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import ClientProfile, Product, Invoice, InvoiceItem
from decimal import Decimal


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="jan", password="haslo")

        if not hasattr(self.user, 'clientprofile'):
            self.profile = ClientProfile.objects.create(
                user=self.user, tax_id="9999999999", address="Testowa 1"
            )
        else:
            self.profile = self.user.clientprofile

        self.product = Product.objects.create(
            name="Monitor",
            price=Decimal("799.99"),
            category="ELEC",
            created_by=self.user
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            status="NEW",
            created_by=self.user
        )

        self.invoice_item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=2,
            price=Decimal("799.99")
        )

    def test_client_profile_str(self):
        self.assertEqual(str(self.profile), f"{self.user.username} ({self.profile.tax_id})")

    def test_product_str(self):
        self.assertEqual(str(self.product), "Monitor: 799.99")

    def test_invoice_str(self):
        self.assertIn("Faktura", str(self.invoice))
        self.assertIn(self.user.username, str(self.invoice))
        self.assertIn(self.invoice.status, str(self.invoice))

    def test_invoice_item_str(self):
        expected = f"{self.product.name} x{self.invoice_item.quantity} dla Faktury #{self.invoice.id}"
        self.assertEqual(str(self.invoice_item), expected)

    def test_invoice_total_price_calculation(self):
        total = self.invoice.items.aggregate_sum = sum(
            [item.quantity * item.price for item in self.invoice.items.all()]
        )
        self.assertEqual(total, Decimal("1599.98"))

# testy API
class InvoiceAPITestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='tom', password='password123')
        self.user2 = User.objects.create_user(username='bob', password='password123')

        self.client.login(username='tom', password='password123')

        self.product = Product.objects.create(
            name="Laptop",
            price=2000,
            category="ELEC",
            created_by=self.user1
        )

    def test_create_product(self):
        response = self.client.post('/invoices/api/products/', {
            "name": "Książka",
            "price": 50.00,
            "category": "BOOK"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "Książka")

    def test_create_invoice_with_items(self):
        payload = {
            "user": self.user1.id,
            "status": "NEW",
            "items": [
                {"product": self.product.id, "quantity": 2, "price": "2000.00"}
            ]
        }
        response = self.client.post('/invoices/api/invoices/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(InvoiceItem.objects.count(), 1)

    def test_retrieve_own_invoice(self):
        invoice = Invoice.objects.create(user=self.user1, status="NEW", created_by=self.user1)
        InvoiceItem.objects.create(invoice=invoice, product=self.product, quantity=1, price=2000)

        response = self.client.get(f'/invoices/api/invoices/{invoice.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_block_access_to_foreign_invoice(self):
        invoice = Invoice.objects.create(user=self.user1, status="NEW", created_by=self.user1)
        InvoiceItem.objects.create(invoice=invoice, product=self.product, quantity=1, price=2000)

        self.client.logout()
        self.client.login(username='bob', password='password123')

        response = self.client.get(f'/invoices/api/invoices/{invoice.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)