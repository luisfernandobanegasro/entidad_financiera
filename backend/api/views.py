from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .services.plan_pago import generar_plan
from reportlab.lib.pagesizes import A4
from rest_framework.permissions import AllowAny
from reportlab.pdfgen import canvas
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
import io
import openpyxl
from django.http import HttpResponse
from .models import (Rol, Permiso, RolPermiso, UserProfile, Bitacora, 
                     Cliente, Empleado,SolicitudCredito, 
                     PlanPago, PlanCuota)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, 
    ChangePasswordSerializer, PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer, RolSerializer, PermisoSerializer,
    RolPermisoSerializer, UserProfileSerializer, BitacoraSerializer,
    ClienteSerializer, EmpleadoSerializer, UserDetailSerializer, ClienteNestedSerializer, EmpleadoNestedSerializer,SolicitudCreateSerializer,
    SolicitudListSerializer,
    SolicitudDetailSerializer,PlanPagoDTO,
    PublicRegisterSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken


# =========================
# User ViewSet
# =========================
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Endpoints públicos:
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer           # admin / backoffice
        elif self.action in ['update','partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserDetailSerializer
        # default
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        ser = UserDetailSerializer(request.user)
        data = ser.data
        # opcional: exponer cliente_id directo
        try:
            data['cliente_id'] = Cliente.objects.get(user=request.user).id
        except Cliente.DoesNotExist:
            data['cliente_id'] = None
        return Response(data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        # campos adicionales que la app móvil necesita
        data['rol_nombre']  = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id']  = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    # =========================
    # Cambiar contraseña
    # =========================
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": ["Contraseña actual incorrecta."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            Bitacora.objects.create(
                usuario=request.user,
                tipo_accion="CAMBIO_CONTRASENA",
                ip=self.get_client_ip(request)
            )
            return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # =========================
    # Reset contraseña
    # =========================
    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
                send_mail(
                    'Restablecimiento de Contraseña',
                    f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response(
                    {"message": "Se ha enviado un enlace para restablecer tu contraseña a tu correo electrónico."},
                    status=status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return Response(
                    {"message": "Si el email existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña."},
                    status=status.HTTP_200_OK
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({"message": "Contraseña restablecida exitosamente."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "El enlace de restablecimiento es inválido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)

    # =========================
    # Listar clientes
    # =========================
    @action(detail=False, methods=['get'])
    def clientes(self, request):
        clientes = User.objects.filter(userprofile__rol__nombre__iexact='cliente')
        page = self.paginate_queryset(clientes)
        if page is not None:
            serializer = UserDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserDetailSerializer(clientes, many=True)
        return Response(serializer.data)

    # =========================
    # Listar empleados
    # =========================
    @action(detail=False, methods=['get'])
    def empleados(self, request):
        # Traer usuarios con rol "administrador" o "personal_credito"
        empleados = User.objects.filter(userprofile__rol__nombre__in=['administrador', 'personal_credito'])
        
        # Ya no usamos select_related('empleado') porque puede no existir
        serializer = UserDetailSerializer(empleados, many=True)
        return Response(serializer.data)
    # Obtener IP del cliente
    # =========================
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# =========================
# Cliente y Empleado ViewSets
# =========================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [permissions.IsAuthenticated]


# =========================
# Resto de viewsets existentes
# =========================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        rol = self.get_object()
        rol_permisos = RolPermiso.objects.filter(rol=rol)
        serializer = RolPermisoSerializer(rol_permisos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_permiso(self, request, pk=None):
        rol = self.get_object()
        permiso_id = request.data.get('permiso_id')
        try:
            permiso = Permiso.objects.get(id=permiso_id)
            rol_permiso, created = RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)
            if created:
                serializer = RolPermisoSerializer(rol_permiso)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({"error": "El permiso ya está asignado a este rol."}, status=status.HTTP_400_BAD_REQUEST)
        except Permiso.DoesNotExist:
            return Response({"error": "Permiso no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['delete'])
    def remove_permiso(self, request, pk=None):
        rol = self.get_object()
        permiso_id = request.data.get('permiso_id')
        try:
            permiso = Permiso.objects.get(id=permiso_id)
            rol_permiso = RolPermiso.objects.get(rol=rol, permiso=permiso)
            rol_permiso.delete()
            return Response({"message": "Permiso eliminado del rol exitosamente."}, status=status.HTTP_204_NO_CONTENT)
        except (Permiso.DoesNotExist, RolPermiso.DoesNotExist):
            return Response({"error": "Permiso no encontrado o no asignado a este rol."}, status=status.HTTP_404_NOT_FOUND)


class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [permissions.IsAuthenticated]


class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            user_profile = serializer.save()
            Bitacora.objects.create(usuario=self.request.user, tipo_accion="CREAR_PERFIL_USUARIO", ip=self.get_client_ip(self.request))

    def perform_update(self, serializer):
        with transaction.atomic():
            user_profile = serializer.save()
            Bitacora.objects.create(usuario=self.request.user, tipo_accion="ACTUALIZAR_PERFIL_USUARIO", ip=self.get_client_ip(self.request))

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bitacora.objects.all()
    serializer_class = BitacoraSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Bitacora.objects.all()
        return Bitacora.objects.filter(usuario=self.request.user)

# Permiso para OFICIAL o ADMIN
class IsOfficialOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Ajusta esto a tu modelo de roles real
        role = getattr(getattr(request.user, 'userprofile', None), 'rol', None)
        nombre = getattr(role, 'nombre', '').upper() if role else ''
        return request.user.is_superuser or nombre in ('OFICIAL', 'ADMIN')

# ====== CU12/CU13/CU14 ======
class SolicitudCreditoViewSet(viewsets.ModelViewSet):
    queryset = SolicitudCredito.objects.filter(is_deleted=False)
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create']:
            return SolicitudCreateSerializer
        elif self.action in ['list']:
            return SolicitudListSerializer
        return SolicitudDetailSerializer

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')

    def perform_create(self, serializer):
        obj = serializer.save()  # estado ENVIADA por defecto

    def list(self, request, *args, **kwargs):
        qs = super().get_queryset()
        cid = request.query_params.get('cliente')
        if cid:
            qs = qs.filter(cliente=cid)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = SolicitudListSerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = SolicitudListSerializer(qs, many=True)
        return Response(ser.data)

    def retrieve(self, request, *args, **kwargs):
        qs = (SolicitudCredito.objects
            .select_related('cliente', 'cliente__user', 'oficial',)
            )
        self.queryset = qs
        return super().retrieve(request, *args, **kwargs)

    # CU13: Evaluar
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsOfficialOrAdmin])
    def evaluar(self, request, pk=None):
        sol = self.get_object()
        score = request.data.get('score_riesgo')
        obs = request.data.get('observacion_evaluacion', '')
        if score is None:
            return Response({"detail": "score_riesgo requerido"}, status=status.HTTP_400_BAD_REQUEST)

        sol.score_riesgo = score
        sol.observacion_evaluacion = obs
        sol.fecha_evaluacion = now()
        if sol.estado in ('ENVIADA', 'DRAFT'):
            sol.estado = 'EVALUADA'
        # asigna oficial si existe relación con el user:
        sol.oficial = Empleado.objects.filter(user=request.user).first() or sol.oficial
        sol.save()
        return Response(SolicitudDetailSerializer(sol).data, status=status.HTTP_200_OK)

    # CU14: Decidir
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOfficialOrAdmin])
    def decidir(self, request, pk=None):
        sol = self.get_object()
        decision = (request.data.get('decision') or '').upper()  # APROBAR | RECHAZAR
        if decision not in ('APROBAR', 'RECHAZAR'):
            return Response({"detail": "decision debe ser APROBAR o RECHAZAR"}, status=status.HTTP_400_BAD_REQUEST)

        if decision == 'APROBAR':
            sol.estado = 'APROBADA'
            sol.fecha_aprobacion = now()
        else:
            sol.estado = 'RECHAZADA'
            sol.fecha_aprobacion = None

        sol.oficial = Empleado.objects.filter(user=request.user).first() or sol.oficial
        sol.save()
        return Response(SolicitudDetailSerializer(sol).data, status=status.HTTP_200_OK)
    

# === CU15: generar plan ===
class PlanPagoGenerateView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOfficialOrAdmin]

    def create(self, request, solicitud_id=None):
        overwrite = str(request.query_params.get('overwrite','false')).lower() == 'true'
        try:
            sol = SolicitudCredito.objects.get(pk=solicitud_id, is_deleted=False)
            plan = generar_plan(sol, request.user, overwrite=overwrite)
            return Response({"plan_id": str(plan.id)}, status=201)
        except SolicitudCredito.DoesNotExist:
            return Response({"detail":"Solicitud no encontrada"}, status=404)
        except ValueError as e:
            return Response({"detail": str(e)}, status=409)

# === CU15: ver plan ===
class PlanPagoDetailView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, solicitud_id=None):
        try:
            plan = PlanPago.objects.select_related('solicitud').prefetch_related('cuotas').get(solicitud_id=solicitud_id)
        except PlanPago.DoesNotExist:
            return Response({"detail":"Plan no encontrado"}, status=404)
        return Response(PlanPagoDTO(plan).data)

# === CU15: export PDF/XLSX ===
class PlanPagoExportView(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, solicitud_id=None):
        fmt = (request.query_params.get('format') or 'pdf').lower()
        try:
            plan = PlanPago.objects.select_related('solicitud').prefetch_related('cuotas').get(solicitud_id=solicitud_id)
        except PlanPago.DoesNotExist:
            return Response({"detail":"Plan no encontrado"}, status=404)

        if fmt == 'xlsx':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Plan"
            ws.append(["#","Vencimiento","Capital","Interés","Cuota","Saldo"])
            for c in plan.cuotas.all():
                ws.append([c.nro_cuota, str(c.fecha_vencimiento), float(c.capital), float(c.interes), float(c.cuota), float(c.saldo)])
            ws.append([])
            ws.append(["Totales","", float(plan.total_capital), float(plan.total_interes), float(plan.total_cuotas), ""])
            bio = io.BytesIO()
            wb.save(bio); bio.seek(0)
            resp = HttpResponse(bio.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp['Content-Disposition'] = f'attachment; filename=plan_{plan.id}.xlsx'
            return resp

        # PDF simple (tabla básica)
        bio = io.BytesIO()
        c = canvas.Canvas(bio, pagesize=A4)
        w, h = A4
        y = h - 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, f"Plan de Pagos – Solicitud {plan.solicitud_id}"); y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(40, y, f"Método: {plan.metodo}  Moneda: {plan.moneda}  Primera cuota: {plan.primera_cuota_fecha}"); y -= 20
        c.drawString(40, y, f"Totales  Capital: {plan.total_capital}  Interés: {plan.total_interes}  Cuotas: {plan.total_cuotas}"); y -= 30
        c.setFont("Helvetica-Bold", 10); c.drawString(40, y, "#  Venc     Capital   Interés   Cuota   Saldo"); y -= 15
        c.setFont("Helvetica", 10)
        for cu in plan.cuotas.all():
            line = f"{cu.nro_cuota:02d} {str(cu.fecha_vencimiento)}  {cu.capital}   {cu.interes}   {cu.cuota}   {cu.saldo}"
            c.drawString(40, y, line); y -= 14
            if y < 60: c.showPage(); y = h - 50
        c.save()
        pdf = bio.getvalue()
        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename=plan_{plan.id}.pdf'
        return resp


class PublicRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)