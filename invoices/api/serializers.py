from rest_framework import serializers
from invoices.models import Product, Invoice, InvoiceItem, ClientProfile
from django.contrib.auth.models import User


class ClientProfileSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'tax_id', 'address']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    profile = ClientProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']

class InvoiceIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'date', 'products']

class UserWithInvoices(serializers.ModelSerializer):
        invoices = InvoiceIdSerializer(many=True, source='invoice_set')

        class Meta:
            model = User
            fields = ['id', 'username', 'invoices']

class ProductSerializer(serializers.ModelSerializer):
    invoice_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['invoice', 'product', 'quantity', 'price']
        extra_kwargs = {
            'invoice': {'required': False},
            'price': {'required': False},  # nie wymagaj price przy tworzeniu
        }

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)
    total_value = serializers.DecimalField(read_only=True, decimal_places=2, max_digits=12)

    class Meta:
        model = Invoice
        fields = '__all__'
        extra_kwargs = {
            'user': {'required': False},  # użytkownik przypisany automatycznie
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        validated_data['user'] = self.context['request'].user  # przypisz użytkownika
        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            product = item_data['product']
            price = item_data.get('price', product.price)  # jeśli brak price, użyj z produktu
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=item_data['quantity'],
                price=price
            )
        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                product = item_data['product']
                price = item_data.get('price', product.price)
                InvoiceItem.objects.create(
                    invoice=instance,
                    product=product,
                    quantity=item_data['quantity'],
                    price=price
                )
        return instance

class InvoiceBasicInfoSerializer(serializers.ModelSerializer):
    total_items = serializers.IntegerField()

    class Meta:
        model = Invoice
        fields = ['id', 'date', 'status', 'total_items']