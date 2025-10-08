from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import PlanPagoGenerateView, PlanPagoDetailView, PlanPagoExportView,PublicRegisterView

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'roles', views.RolViewSet)
router.register(r'permisos', views.PermisoViewSet)
router.register(r'rol-permisos', views.RolPermisoViewSet)
router.register(r'user-profiles', views.UserProfileViewSet)
router.register(r'bitacora', views.BitacoraViewSet)

# Nuevos endpoints para Clientes, Empleados y Solicitudes de Crédito
router.register(r'clientes', views.ClienteViewSet)
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'solicitudes', views.SolicitudCreditoViewSet)


urlpatterns = [
    path('', include(router.urls)),
    # CU15:
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/', PlanPagoDetailView.as_view({'get':'list'}), name='plan-detail'),
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/generar', PlanPagoGenerateView.as_view({'post':'create'}), name='plan-generate'),
    path('solicitudes/<uuid:solicitud_id>/plan-pagos/export', PlanPagoExportView.as_view({'get':'list'}), name='plan-export'),
    
    path('auth/password-reset/', views.UserViewSet.as_view({'post': 'password_reset_request'}), name='password-reset'),
    path('auth/password-reset-confirm/<uidb64>/<token>/', views.UserViewSet.as_view({'post': 'password_reset_confirm'}), name='password-reset-confirm'),
    path('auth/register/', PublicRegisterView.as_view(), name='register-public'),

]