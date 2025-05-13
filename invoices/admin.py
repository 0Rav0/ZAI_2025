from django.contrib import admin
from invoices.models import *

admin.site.register(ClientProfile)

admin.site.register(Invoice)
admin.site.register(InvoiceItem)
admin.site.register(Product)
