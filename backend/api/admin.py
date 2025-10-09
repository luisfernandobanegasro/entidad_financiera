from django.contrib import admin

# Register your models here.
from .models import ProductoFinanciero, DocumentoTipo, RequisitoProductoDocumento, DocumentoAdjunto
admin.site.register(ProductoFinanciero)
admin.site.register(DocumentoTipo)
admin.site.register(RequisitoProductoDocumento)
admin.site.register(DocumentoAdjunto)
