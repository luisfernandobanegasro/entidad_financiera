# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, RolViewSet, PermisoViewSet, RolPermisoViewSet,
    UserProfileViewSet, BitacoraViewSet,
    ClienteViewSet, EmpleadoViewSet, SolicitudCreditoViewSet,
    ProductoFinancieroViewSet, DocumentoAdjuntoViewSet,
    DocumentoTipoViewSet, RequisitoProductoDocumentoViewSet,
    PlanPagoGenerateView, PlanPagoDetailView, PlanPagoExportView,
    PublicRegisterView, SimuladorAPIView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RolViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'rol-permisos', RolPermisoViewSet)
router.register(r'user-profiles', UserProfileViewSet)
router.register(r'bitacora', BitacoraViewSet)

# CRUD principales
router.register(r'clientes', ClienteViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'solicitudes', SolicitudCreditoViewSet)

# Productos / Documentos
router.register(r'productos', ProductoFinancieroViewSet, basename='productos')
router.register(r'documentos', DocumentoAdjuntoViewSet, basename='documentos')
router.register(r'documento-tipos', DocumentoTipoViewSet, basename='documento-tipos')
router.register(r'requisitos', RequisitoProductoDocumentoViewSet, basename='requisitos')

urlpatterns = [
    # Router
    path('', include(router.urls)),

    # CU15: Plan de pago
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/', PlanPagoDetailView.as_view({'get': 'list'}), name='plan-detail'),
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/generar/', PlanPagoGenerateView.as_view({'post': 'create'}), name='plan-generate'),
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/export/', PlanPagoExportView.as_view({'get': 'list'}), name='plan-export'),

    # Auth utilidades
    path('auth/password-reset/', UserViewSet.as_view({'post': 'password_reset_request'}), name='password-reset'),
    path('auth/password-reset-confirm/<uidb64>/<token>/', UserViewSet.as_view({'post': 'password_reset_confirm'}), name='password-reset-confirm'),
    path('auth/register/', PublicRegisterView.as_view(), name='register-public'),

    # CU11: Simulador
    path('simulador/', SimuladorAPIView.as_view(), name='simulador'),
]
