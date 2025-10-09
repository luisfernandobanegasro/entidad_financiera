# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # ViewSets principales (router)
    UserViewSet, RolViewSet, PermisoViewSet, RolPermisoViewSet,
    UserProfileViewSet, BitacoraViewSet,
    ClienteViewSet, EmpleadoViewSet, SolicitudCreditoViewSet,
    ProductoFinancieroViewSet, DocumentoAdjuntoViewSet,
    DocumentoTipoViewSet, RequisitoProductoDocumentoViewSet,

    # Plan de pagos (endpoints manuales SOLO para listar/generar)
    PlanPagoGenerateView, PlanPagoDetailView,

    # Otros endpoints sueltos
    PublicRegisterView, SimuladorAPIView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RolViewSet)
router.register(r'permisos', PermisoViewSet)
router.register(r'rol-permisos', RolPermisoViewSet)
router.register(r'user-profiles', UserProfileViewSet)
router.register(r'bitacora', BitacoraViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'solicitudes', SolicitudCreditoViewSet)  # <- aquí está la @action export
router.register(r'productos', ProductoFinancieroViewSet, basename='productos')
router.register(r'documentos', DocumentoAdjuntoViewSet, basename='documentos')
router.register(r'documento-tipos', DocumentoTipoViewSet, basename='documento-tipos')
router.register(r'requisitos', RequisitoProductoDocumentoViewSet, basename='requisitos')

urlpatterns = [
    # —— PLAN DE PAGO (detalle + generar) ——
    path(
        'solicitudes/<uuid:solicitud_id>/plan-pagos/',
        PlanPagoDetailView.as_view({'get': 'list'}),
        name='plan-detail'
    ),
    path(
        'solicitudes/<uuid:solicitud_id>/plan-pagos/generar/',
        PlanPagoGenerateView.as_view({'post': 'create'}),
        name='plan-generate'
    ),
    # Nota: NO se declara path para export; lo expone el router via @action.

    # —— Auth / registro público ——
    path('auth/password-reset/', UserViewSet.as_view({'post': 'password_reset_request'})),
    path('auth/password-reset-confirm/<uidb64>/<token>/', UserViewSet.as_view({'post': 'password_reset_confirm'})),
    path('auth/register/', PublicRegisterView.as_view()),

    # —— Simulador ——
    path('simulador/', SimuladorAPIView.as_view()),

    # —— Router (al final) ——
    path('', include(router.urls)),
]
