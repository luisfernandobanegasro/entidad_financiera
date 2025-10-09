# backend/api/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from django.utils.timezone import now
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

import io
import openpyxl

from .services.plan_pago import generar_plan
from .services.simulador import simular_plan
from .services.validadores import validar_vigencia

from .models import (
    Rol, Permiso, RolPermiso, UserProfile, Bitacora,
    Cliente, Empleado, SolicitudCredito,
    PlanPago, ProductoFinanciero,
    DocumentoTipo, RequisitoProductoDocumento, DocumentoAdjunto,
)

from .serializers import (
    # Usuarios
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UserDetailSerializer, UserProfileSerializer, PublicRegisterSerializer,

    # Roles / Permisos / Bitácora
    RolSerializer, PermisoSerializer, RolPermisoSerializer, BitacoraSerializer,

    # Personas
    ClienteSerializer, EmpleadoSerializer,
    ClienteNestedSerializer, EmpleadoNestedSerializer,

    # Solicitudes
    SolicitudCreateSerializer, SolicitudListSerializer, SolicitudDetailSerializer,

    # Plan pago
    PlanPagoDTO,

    # Productos / Documentos
    ProductoFinancieroSerializer, DocumentoAdjuntoSerializer, DocumentoTipoSerializer,
    RequisitoProductoDocumentoSerializer, RequisitoProductoDocumentoWriteSerializer,
)

# =========================================================
#                    PERMISOS DE NEGOCIO
# =========================================================
class IsOfficialOrAdmin(permissions.BasePermission):
    """Permite acceso a superuser o a usuarios con rol OFICIAL/ADMIN en UserProfile."""
    def has_permission(self, request, view):
        role = getattr(getattr(request.user, 'userprofile', None), 'rol', None)
        nombre = getattr(role, 'nombre', '').upper() if role else ''
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_superuser or nombre in ('OFICIAL', 'ADMIN'))
        )

# =========================================================
#                          USUARIOS
# =========================================================
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register_public', 'password_reset_request', 'password_reset_confirm']:
            return [AllowAny()]
        return [perm() for perm in self.permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        if self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        u = request.user
        data = UserSerializer(u).data
        cli = Cliente.objects.filter(user=u).first()
        emp = Empleado.objects.filter(user=u).first()
        data['rol_nombre'] = getattr(getattr(u, 'userprofile', None), 'rol', None) and u.userprofile.rol.nombre
        data['cliente_id'] = cli.id if cli else None
        data['empleado_id'] = emp.id if emp else None
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register_public(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=status.HTTP_201_CREATED)

    # -------- Password --------
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"old_password": ["Contraseña actual incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        Bitacora.objects.create(
            usuario=request.user,
            tipo_accion="CAMBIO_CONTRASENA",
            ip=self.get_client_ip(request)
        )
        return Response({"message": "Contraseña cambiada exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/password-reset-confirm/{uid}/{token}/"
            send_mail(
                'Restablecimiento de Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}',
                settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
            )
        except User.DoesNotExist:
            pass
        return Response({"message": "Si el email existe, recibirás un enlace para restablecer tu contraseña."}, status=200)

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace es inválido o ha expirado."}, status=400)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=200)

    def get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR')

# =========================================================
#                    CLIENTE / EMPLEADO
# =========================================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [IsAuthenticated]

# =========================================================
#              ROLES / PERMISOS / BITÁCORA
# =========================================================
class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        rol = self.get_object()
        ser = RolPermisoSerializer(RolPermiso.objects.filter(rol=rol), many=True)
        return Response(ser.data)

    @action(detail=True, methods=['post'])
    def add_permiso(self, request, pk=None):
        rol = self.get_object()
        permiso_id = request.data.get('permiso_id')
        try:
            permiso = Permiso.objects.get(id=permiso_id)
            rp, created = RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)
            if created:
                return Response(RolPermisoSerializer(rp).data, status=201)
            return Response({"error": "El permiso ya está asignado."}, status=400)
        except Permiso.DoesNotExist:
            return Response({"error": "Permiso no encontrado."}, status=404)

    @action(detail=True, methods=['delete'])
    def remove_permiso(self, request, pk=None):
        rol = self.get_object()
        permiso_id = request.data.get('permiso_id')
        try:
            permiso = Permiso.objects.get(id=permiso_id)
            rp = RolPermiso.objects.get(rol=rol, permiso=permiso)
            rp.delete()
            return Response(status=204)
        except (Permiso.DoesNotExist, RolPermiso.DoesNotExist):
            return Response({"error": "Permiso no encontrado o no asignado."}, status=404)

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.all()
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]

class RolPermisoViewSet(viewsets.ModelViewSet):
    queryset = RolPermiso.objects.all()
    serializer_class = RolPermisoSerializer
    permission_classes = [IsAuthenticated]

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save()
            Bitacora.objects.create(
                usuario=self.request.user,
                tipo_accion="CREAR_PERFIL_USUARIO",
                ip=self.request.META.get('REMOTE_ADDR')
            )

    def perform_update(self, serializer):
        with transaction.atomic():
            serializer.save()
            Bitacora.objects.create(
                usuario=self.request.user,
                tipo_accion="ACTUALIZAR_PERFIL_USUARIO",
                ip=self.request.META.get('REMOTE_ADDR')
            )

class BitacoraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bitacora.objects.all()
    serializer_class = BitacoraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Bitacora.objects.all()
        return Bitacora.objects.filter(usuario=self.request.user)

# =========================================================
#                 SOLICITUDES (CU12/13/14)
# =========================================================
class SolicitudCreditoViewSet(viewsets.ModelViewSet):
    queryset = SolicitudCredito.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return SolicitudCreateSerializer
        if self.action == 'list':
            return SolicitudListSerializer
        return SolicitudDetailSerializer

    def list(self, request, *args, **kwargs):
        qs = super().get_queryset()
        cid = request.query_params.get('cliente')
        if cid:
            qs = qs.filter(cliente=cid)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(SolicitudListSerializer(page, many=True).data)
        return Response(SolicitudListSerializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        self.queryset = (SolicitudCredito.objects
                         .select_related('cliente', 'cliente__user', 'oficial'))
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        obj = serializer.save()
        if not obj.estado:
            obj.estado = 'ENVIADA'
            obj.save(update_fields=['estado'])

    # ---- CU13: Evaluar ----
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsOfficialOrAdmin])
    def evaluar(self, request, pk=None):
        sol = self.get_object()
        score = request.data.get('score_riesgo')
        obs = request.data.get('observacion_evaluacion', '')
        if score is None:
            return Response({"detail": "score_riesgo requerido"}, status=400)

        sol.score_riesgo = score
        sol.observacion_evaluacion = obs
        sol.fecha_evaluacion = now()
        if sol.estado in ('ENVIADA', 'DRAFT'):
            sol.estado = 'EVALUADA'
        sol.oficial = Empleado.objects.filter(user=request.user).first() or sol.oficial
        sol.save()
        return Response(SolicitudDetailSerializer(sol).data)

    # ---- CU14: Decidir ----
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOfficialOrAdmin])
    def decidir(self, request, pk=None):
        sol = self.get_object()
        decision = (request.data.get('decision') or '').upper()
        if decision not in ('APROBAR', 'RECHAZAR'):
            return Response({"detail": "decision debe ser APROBAR o RECHAZAR"}, status=400)

        if decision == 'APROBAR':
            sol.estado = 'APROBADA'
            sol.fecha_aprobacion = now()
        else:
            sol.estado = 'RECHAZADA'
            sol.fecha_aprobacion = None

        sol.oficial = Empleado.objects.filter(user=request.user).first() or sol.oficial
        sol.save()
        return Response(SolicitudDetailSerializer(sol).data)

    # ---- Checklist para front ----
    @action(detail=True, methods=['get'], url_path='documentos/checklist')
    def checklist(self, request, pk=None):
        sol = self.get_object()
        if not sol.producto or not sol.tipo_trabajador:
            return Response({'detail': 'Solicitud sin producto o tipo_trabajador'}, status=400)

        reqs = (RequisitoProductoDocumento.objects
                .select_related('documento')
                .filter(producto=sol.producto, tipo_trabajador=sol.tipo_trabajador))

        adjuntos = {a.documento_tipo_id: a for a in sol.documentos.all()}
        items = []
        for r in reqs:
            a = adjuntos.get(r.documento.id)
            items.append({
                'codigo': r.documento.codigo,
                'nombre': r.documento.nombre,
                'obligatorio': r.obligatorio,
                'recibido': bool(a),
                'valido': None if not a else a.valido,
                'motivo': None if not a else (a.observacion or None),
                'adjunto_id': None if not a else a.id,
                'archivo_url': None if not a or not a.archivo else a.archivo.url,
                'fecha_emision': None if not a else a.fecha_emision,
                'documento_tipo_id': r.documento.id,
            })
        return Response(items)

    @action(detail=True, methods=['get'], url_path='seguimiento', permission_classes=[IsAuthenticated])
    def seguimiento(self, request, pk=None):
        sol = self.get_object()
        timeline = [
            {'evento': 'CREADA', 'fecha': sol.created_at},
            {'evento': f'ESTADO_{sol.estado}', 'fecha': sol.updated_at},
        ]
        return Response({'estadoActual': sol.estado, 'timelineEstados': timeline})

    # ---- Exportar plan (PDF/XLSX) ----
    @action(detail=True, methods=['get'], url_path='plan-pagos/export', permission_classes=[IsAuthenticated])
    def export_plan(self, request, pk=None):
        fmt = (request.query_params.get('format') or 'pdf').lower()
        try:
            plan = (PlanPago.objects
                    .select_related('solicitud')
                    .prefetch_related('cuotas')
                    .get(solicitud_id=pk))
        except PlanPago.DoesNotExist:
            return Response({"detail": "Plan no encontrado"}, status=404)

        if fmt == 'xlsx':
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Plan"
            ws.append(["#", "Vencimiento", "Capital", "Interés", "Cuota", "Saldo"])
            for c in plan.cuotas.all():
                ws.append([
                    c.nro_cuota, str(c.fecha_vencimiento),
                    float(c.capital), float(c.interes),
                    float(c.cuota), float(c.saldo)
                ])
            ws.append([])
            ws.append(["Totales", "", float(plan.total_capital),
                       float(plan.total_interes), float(plan.total_cuotas), ""])
            bio = io.BytesIO()
            wb.save(bio)
            bio.seek(0)
            resp = HttpResponse(
                bio.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            resp['Content-Disposition'] = f'attachment; filename=plan_{plan.id}.xlsx'
            return resp

        # PDF
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
            if y < 60:
                c.showPage(); y = h - 50
        c.save()
        pdf = bio.getvalue()
        resp = HttpResponse(pdf, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename=plan_{plan.id}.pdf'
        return resp

# =========================================================
#                    PLAN DE PAGO (CU15)
# =========================================================
class PlanPagoGenerateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsOfficialOrAdmin]

    def create(self, request, solicitud_id=None):
        overwrite = str(request.query_params.get('overwrite', 'false')).lower() == 'true'
        try:
            sol = SolicitudCredito.objects.get(pk=solicitud_id, is_deleted=False)
            plan = generar_plan(sol, request.user, overwrite=overwrite)
            return Response({"plan_id": str(plan.id)}, status=201)
        except SolicitudCredito.DoesNotExist:
            return Response({"detail": "Solicitud no encontrada"}, status=404)
        except ValueError as e:
            return Response({"detail": str(e)}, status=409)

class PlanPagoDetailView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, solicitud_id=None):
        try:
            plan = (PlanPago.objects
                    .select_related('solicitud')
                    .prefetch_related('cuotas')
                    .get(solicitud_id=solicitud_id))
        except PlanPago.DoesNotExist:
            return Response({"detail": "Plan no encontrado"}, status=404)
        return Response(PlanPagoDTO(plan).data)

# (Ojo: NO hay PlanPagoExportView; la exportación la maneja export_plan de SolicitudCreditoViewSet)

# =========================================================
#                     REGISTRO PÚBLICO
# =========================================================
class PublicRegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = PublicRegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(ser.to_representation(user), status=201)

# =========================================================
#                       CU11: SIMULADOR
# =========================================================
class SimuladorAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        try:
            monto = float(request.data.get('monto'))
            plazo = int(request.data.get('plazo_meses'))
            tna = float(request.data.get('tasa_nominal_anual'))
            primera = request.data.get('primera_cuota_fecha')  # opcional ISO
        except Exception:
            return Response({'detail': 'Parámetros inválidos'}, status=400)
        plan, cuotas = simular_plan(monto, plazo, tna, primera)
        return Response({'resumen': plan, 'cuotas': cuotas})

# =========================================================
#                 CU18: PRODUCTOS / DOCUMENTOS
# =========================================================
class ProductoFinancieroViewSet(viewsets.ModelViewSet):
    queryset = ProductoFinanciero.objects.all()
    serializer_class = ProductoFinancieroSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='requisitos', permission_classes=[permissions.AllowAny])
    def requisitos(self, request, pk=None):
        tipo = request.query_params.get('tipo_trabajador')
        if tipo not in ['PUBLICO', 'PRIVADO', 'INDEPENDIENTE']:
            return Response({'detail': 'tipo_trabajador inválido'}, status=400)
        producto = self.get_object()
        reqs = (RequisitoProductoDocumento.objects
                .select_related('documento')
                .filter(producto=producto, tipo_trabajador=tipo))
        data = [{
            'documento': {
                'codigo': r.documento.codigo,
                'nombre': r.documento.nombre,
                'vigencia_dias': r.documento.vigencia_dias
            },
            'obligatorio': r.obligatorio
        } for r in reqs]
        return Response(data)

class DocumentoTipoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoTipo.objects.all().order_by('nombre')
    serializer_class = DocumentoTipoSerializer
    permission_classes = [IsAuthenticated]

class RequisitoProductoDocumentoViewSet(viewsets.ModelViewSet):
    queryset = RequisitoProductoDocumento.objects.select_related('producto', 'documento').all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RequisitoProductoDocumentoWriteSerializer
        return RequisitoProductoDocumentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        prod = self.request.query_params.get('producto')
        tipo = self.request.query_params.get('tipo_trabajador')
        if prod:
            qs = qs.filter(producto_id=prod)
        if tipo in ['PUBLICO', 'PRIVADO', 'INDEPENDIENTE']:
            qs = qs.filter(tipo_trabajador=tipo)
        return qs

# =========================================================
#                 CU19: DOCUMENTOS ADJUNTOS
# =========================================================
class DocumentoAdjuntoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoAdjunto.objects.select_related('documento_tipo', 'solicitud')
    serializer_class = DocumentoAdjuntoSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def create(self, request, *args, **kwargs):
        solicitud_id = request.data.get('solicitud')
        doc_tipo_id = request.data.get('documento_tipo')
        if not solicitud_id or not doc_tipo_id:
            return Response({'detail': 'solicitud y documento_tipo son requeridos'}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        adj = serializer.save()

        doc_tipo = adj.documento_tipo
        is_valid, motivo = validar_vigencia(adj.fecha_emision, doc_tipo.vigencia_dias)
        adj.valido = is_valid
        adj.observacion = '' if is_valid else (motivo or '')
        adj.save()

        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(adj).data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        adj = serializer.save()

        doc_tipo = adj.documento_tipo
        is_valid, motivo = validar_vigencia(adj.fecha_emision, doc_tipo.vigencia_dias)
        adj.valido = is_valid
        adj.observacion = '' if is_valid else (motivo or '')
        adj.save()
        return Response(self.get_serializer(adj).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        f = instance.archivo
        resp = super().destroy(request, *args, **kwargs)
        try:
            if f and f.storage.exists(f.name):
                f.storage.delete(f.name)
        except Exception:
            pass
        return resp
