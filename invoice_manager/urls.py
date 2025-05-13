from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path('invoices/', include('invoices.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

