from django.contrib.auth.models import User
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Count
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters, generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny

from invoices.models import Product, Invoice, InvoiceItem, ClientProfile
from .serializers import UserSerializer, ProductSerializer, InvoiceSerializer, UserCreateSerializer, \
    ClientProfileSerializer, InvoiceBasicInfoSerializer, UserWithInvoices

from .permissions import IsOwnerOrAdmin, IsSelfOrAdmin


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'is_staff']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class ClientProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientProfileSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]

    def get_object(self):
        user = self.request.user

        if user.is_staff and 'user_id' in self.request.query_params:
            # pozwól adminowi edytować dowolny profil przez ?user_id=
            user_id = self.request.query_params['user_id']
            return ClientProfile.objects.get(user__id=user_id)

        # użytkownik widzi tylko swój profil
        return ClientProfile.objects.get(user=user)

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [FormParser, MultiPartParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class InvoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        qs = Invoice.objects.annotate(
            total_value=Sum(
                ExpressionWrapper(F('items__quantity') * F('items__price'), output_field=DecimalField())
            )
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user, status="NEW")

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        qs = Invoice.objects.annotate(
            total_value=Sum(
                ExpressionWrapper(F('items__quantity') * F('items__price'), output_field=DecimalField())
            )
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class UsersWithPaidInvoices(generics.ListAPIView):  # nie działa
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(invoice__status='PAID').distinct()

class UsersWithInvoices(generics.ListAPIView):
    serializer_class = UserWithInvoices
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(invoice__isnull=False).distinct()

class UsersWithClientProfil(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(clientprofile__isnull=False)

class ProductsInInvoices(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        produkty_ids = InvoiceItem.objects.values_list('product', flat=True)
        return Product.objects.filter(id__in=produkty_ids).distinct()

class ProductsNotInInvoices(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        produkty_ids = InvoiceItem.objects.values_list('product', flat=True)
        return Product.objects.exclude(id__in=produkty_ids)

class ProductsByUserInvoices(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        products = Product.objects.filter(invoiceitem__invoice__user_id=user_id).distinct()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class PopularProducts(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.annotate(
            invoice_count=Count('invoiceitem')
        ).filter(invoice_count__gt=1).order_by('-invoice_count')

class InvoiceBasicInfoListView(generics.ListAPIView):
    serializer_class = InvoiceBasicInfoSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Invoice.objects.annotate(total_items=Count('items'))

class APIRootView(APIView):
    """
    Widok główny API Root dla SimpleRouter
    """
    def get(self, request, format=None):
        total_products = Product.objects.count()
        total_invoices = Invoice.objects.count()
        total_invoice_value = Invoice.objects.annotate(
            total_value=Sum(
                ExpressionWrapper(F('items__quantity') * F('items__price'), output_field=DecimalField())
            )
        ).aggregate(Sum('total_value'))['total_value__sum'] or 0  # Domyślna wartość 0, jeśli brak faktur

        return Response({
            'token': reverse('token_obtain_pair', request=request, format=format),

            'użytkownicy': reverse('user-list', request=request, format=format),
            'produkty': reverse('product-list-create', request=request, format=format),
            'faktury': reverse('invoice-list-create', request=request, format=format),
            'profil': reverse('my-profile', request=request, format=format),

            'GET użytkownicy z profilem klienta': reverse('users-with-clientprofile', request=request, format=format),
            'GET użytkownicy z fakturami': reverse('users-with-invoices', request=request, format=format),
            'GET użytkownicy z zapłaconymi fakturami': reverse('users-paid', request=request, format=format),
            'GET produkty w fakturach': reverse('products-in-invoices', request=request, format=format),
            'GET produkty bez faktur': reverse('products-not-in-invoices', request=request, format=format),
            'GET produkty w fakturach użytkownika': "products-by-use/id/r",
            'GET popularne produkty': reverse('popular-products', request=request, format=format),
            'GET podstawowe info faktury': reverse('invoice-basic-info', request=request, format=format),

            'ilość produktów': total_products,
            'ilość faktur': total_invoices,
            'suma wartości faktur': total_invoice_value,

        })