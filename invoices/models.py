from django.db import models
from django.contrib.auth.models import User


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tax_id = models.CharField(max_length=20)
    address = models.TextField()

    def __str__(self):
        return f"{self.user.username} ({self.tax_id})"

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profile"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('ELEC', 'Elektronika'),
        ('BOOK', 'Książki'),
        ('FOOD', 'Jedzenie'),
        ('OTHR', 'Inne'),
    ]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    desc = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='produkty/', blank=True, null=True)
    category = models.CharField(max_length=4, choices=CATEGORY_CHOICES, default='OTHR')
    created_by = models.ForeignKey(User, related_name='created_products', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='updated_products', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}: {self.price}"

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, default='NEW')
    products = models.ManyToManyField(Product, through='InvoiceItem')
    created_by = models.ForeignKey(User, related_name='created_invoices', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='updated_invoices', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Faktura #{self.id} - {self.user.username} - {self.status}"

    class Meta:
        verbose_name = "Faktura"
        verbose_name_plural = "Faktury"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} dla Faktury #{self.invoice.id}"

    class Meta:
        verbose_name = "Pozycja"
        verbose_name_plural = "Pozycje"