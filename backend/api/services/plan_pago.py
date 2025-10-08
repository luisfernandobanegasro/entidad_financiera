from decimal import Decimal, ROUND_HALF_UP, getcontext
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now
from ..models import PlanPago, PlanCuota, SolicitudCredito
from django.db import transaction

getcontext().prec = 28
Q2 = Decimal("0.01")

def q2(x): return Decimal(x).quantize(Q2, rounding=ROUND_HALF_UP)

def generar_plan(solicitud: SolicitudCredito, usuario, overwrite=False):
    if solicitud.estado != 'APROBADA':
        raise ValueError("La solicitud no está APROBADA.")

    if overwrite and hasattr(solicitud, "plan"):
        solicitud.plan.delete()

    elif not overwrite and hasattr(solicitud, "plan"):
        raise ValueError("El plan ya existe. Use overwrite=true para regenerar.")

    P = Decimal(solicitud.monto)
    n = int(solicitud.plazo_meses)
    r = Decimal(solicitud.tasa_nominal_anual) / Decimal("1200")  # mensual

    # PMT francés
    pmt = P * r / (Decimal(1) - (Decimal(1) + r) ** (-n))
    pmt = q2(pmt)

    base_date = solicitud.fecha_aprobacion.date() if solicitud.fecha_aprobacion else now().date()
    fecha = base_date + relativedelta(months=+1)

    cuotas = []
    saldo = P
    tot_cap = Decimal("0.00")
    tot_int = Decimal("0.00")
    ajuste_total = Decimal("0.00")

    for k in range(1, n + 1):
        interes = q2(saldo * r)
        capital = q2(pmt - interes)
        cuota_k = pmt

        if k == n:
            # Ajuste final para que saldo cierre en 0.00
            capital = q2(saldo)
            cuota_k = q2(capital + interes)
            # Ajuste (informativo)
            ajuste_total = q2((P + tot_int + interes) - (pmt * (n - 1) + cuota_k))

        saldo = q2(saldo - capital)

        cuotas.append({
            "nro_cuota": k,
            "fecha": fecha,
            "capital": capital,
            "interes": interes,
            "cuota": cuota_k,
            "saldo": saldo,
            "ajuste": Decimal("0.00") if k < n else ajuste_total
        })
        fecha = fecha + relativedelta(months=+1)
        tot_cap += capital
        tot_int += interes

    with transaction.atomic():
        plan = PlanPago.objects.create(
            solicitud=solicitud,
            metodo='frances',
            moneda=solicitud.moneda,
            primera_cuota_fecha=cuotas[0]["fecha"],
            total_capital=q2(tot_cap),
            total_interes=q2(tot_int),
            total_cuotas=q2(tot_cap + tot_int),
            redondeo_ajuste_total=q2(ajuste_total),
            generado_por=usuario
        )
        for c in cuotas:
            PlanCuota.objects.create(
                plan=plan,
                nro_cuota=c["nro_cuota"],
                fecha_vencimiento=c["fecha"],
                capital=c["capital"],
                interes=c["interes"],
                cuota=c["cuota"],
                saldo=c["saldo"],
                ajuste_redondeo=c["ajuste"],
            )
    return plan
