from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, InvoiceListCreateView, InvoiceDetailView, ProductListCreateView, \
    ProductDetailView, APIRootView, ClientProfileDetailView, UsersWithPaidInvoices, ProductsInInvoices, \
    ProductsNotInInvoices, UsersWithInvoices, UsersWithClientProfil, PopularProducts, \
    ProductsByUserInvoices, InvoiceBasicInfoListView

router = SimpleRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # APIRoot
    path('', APIRootView.as_view(), name='api-root'),
    path('', include(router.urls)),

    # Token
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # CRUD
    path('profile/', ClientProfileDetailView.as_view(), name='my-profile'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('invoices/', InvoiceListCreateView.as_view(), name='invoice-list-create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),

    # Dodatkowe
    path('users-paid/', UsersWithPaidInvoices.as_view(), name='users-paid'),
    path('users-with-invoices/', UsersWithInvoices.as_view(), name='users-with-invoices'),
    path('users-with-clientprofil/', UsersWithClientProfil.as_view(), name='users-with-clientprofile'),
    path('products-in-invoices/', ProductsInInvoices.as_view(), name='products-in-invoices'),
    path('products-not-invoices/', ProductsNotInInvoices.as_view(), name='products-not-in-invoices'),
    path('products-by-user/<int:user_id>/', ProductsByUserInvoices.as_view(), name='products-by-user'),
    path('products/popular/', PopularProducts.as_view(), name='popular-products'),
    path('invoices-simple/', InvoiceBasicInfoListView.as_view(), name='invoice-basic-info'),

]
