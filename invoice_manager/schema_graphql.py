import graphene
from django.db.models import Count
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required

from invoices.models import Product, Invoice, InvoiceItem
from django.contrib.auth.models import User
import graphql_jwt


# Typy obiektów
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product


class InvoiceItemType(DjangoObjectType):
    class Meta:
        model = InvoiceItem


class InvoiceType(DjangoObjectType):
    class Meta:
        model = Invoice


# Mutacja do dodania produktu przez zalogowanego użytkownika
class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        name = graphene.String(required=True)
        desc = graphene.String()
        price = graphene.Decimal(required=True)

    def mutate(self, info, name, price, desc="", user=None):
        product = Product.objects.create(
            name=name,
            desc=desc,
            price=price,
            created_by=User.objects.get(id=1)
        )
        return CreateProduct(product=product)


# Mutacje główne
class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    create_product = CreateProduct.Field()

# Główne zapytania
class Query(graphene.ObjectType):
    all_products = graphene.List(ProductType)
    all_invoices = graphene.List(InvoiceType)
    all_users = graphene.List(UserType)

    # Dodatkowe widoki jako zapytania
    products_in_invoices = graphene.List(ProductType)
    products_not_in_invoices = graphene.List(ProductType)
    products_by_user_invoices = graphene.List(ProductType, user_id=graphene.Int())

    users_with_paid_invoices = graphene.List(UserType)
    users_with_invoices = graphene.List(UserType)
    users_with_client_profile = graphene.List(UserType)
    popular_products = graphene.List(ProductType)
    invoice_basic_info = graphene.List(InvoiceType)

    def resolve_all_products(root, info):
        return Product.objects.all()

    @login_required
    def resolve_all_invoices(root, info):
        user = info.context.user
        if user.is_staff:
            return Invoice.objects.all()
        return Invoice.objects.filter(user=user)

    @login_required
    def resolve_all_users(root, info):
        return User.objects.all()

    @login_required
    def resolve_users_with_paid_invoices(root, info):
        return User.objects.filter(invoice__status='PAID').distinct()

    @login_required
    def resolve_users_with_invoices(root, info):
        return User.objects.filter(invoice__isnull=False).distinct()

    @login_required
    def resolve_users_with_client_profile(root, info):
        return User.objects.filter(clientprofile__isnull=False)

    @login_required
    def resolve_products_in_invoices(root, info):
        produkt_ids = InvoiceItem.objects.values_list('product', flat=True)
        return Product.objects.filter(id__in=produkt_ids).distinct()

    @login_required
    def resolve_products_not_in_invoices(root, info):
        produkt_ids = InvoiceItem.objects.values_list('product', flat=True)
        return Product.objects.exclude(id__in=produkt_ids)

    @login_required
    def resolve_products_by_user_invoices(root, info, user_id):
        return Product.objects.filter(invoiceitem__invoice__user_id=user_id).distinct()

    def resolve_popular_products(root, info):
        return Product.objects.annotate(
            invoice_count=Count('invoiceitem')
        ).filter(invoice_count__gt=1).order_by('-invoice_count')

    @login_required
    def resolve_invoice_basic_info(root, info):
        return Invoice.objects.annotate(total_items=Count('items'))

    viewer = graphene.Field(UserType)

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication credentials were not provided")
        return user

# Schema z zapytaniami i mutacjami
schema = graphene.Schema(query=Query, mutation=Mutation)
