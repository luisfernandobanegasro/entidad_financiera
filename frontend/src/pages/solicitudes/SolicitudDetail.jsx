import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSolicitud, evaluarSolicitud, decidirSolicitud } from '../../services/solicitudes';

export default function SolicitudDetail() {
  const { id } = useParams();
  const [row, setRow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  // acciones
  const [score, setScore] = useState('');
  const [obs, setObs] = useState('');
  const [errEval, setErrEval] = useState('');
  const [errDec, setErrDec] = useState('');

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getSolicitud(id);
      setRow(data);
      setErr('');
    } catch (e) {
      setErr('No se pudo cargar la solicitud.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // src/pages/solicitudes/SolicitudDetail.jsx
const doEvaluar = async () => {
  try {
    setErrEval('');
    await evaluarSolicitud(id, {
      score_riesgo: Number(score),                   // ← opcional, pero recomendado
      observacion_evaluacion: obs || '',
    });
    await load();
  } catch (e) {
    setErrEval(String(e?.response?.data?.detail || e));
  }
};

const doDecidir = async (decision) => {
  try {
    setErrDec('');
    await decidirSolicitud(id, decision);           // ← pasa el string plano
    await load();
  } catch (e) {
    setErrDec(String(e?.response?.data?.detail || e));
  }
};


  if (loading) return <div>Cargando…</div>;
  if (err) return <div style={{ color: 'crimson' }}>{err}</div>;
  if (!row) return <div>No encontrado</div>;

  // Panel de datos del cliente (toma del backend si existe; si no, arma con cliente_info)
  const panel = row.cliente_panel || {};
  const nombre =
    panel.nombre ||
    `${row.cliente_info?.user_info?.first_name || ''} ${row.cliente_info?.user_info?.last_name || ''}`.trim() ||
    row.cliente_nombre ||
    `Cliente #${row.cliente}`;
  const email =
    panel.email ||
    row.cliente_info?.user_info?.email ||
    '';
  const doc =
    panel.documento ||
    `${row.cliente_info?.tipo_documento || ''} ${row.cliente_info?.numero_documento || ''}`.trim();

  return (
    <div className="wrap">
      <div className="header">
        <div>
          <h2>
            Solicitud <span className="mono">#{row.id}</span>
          </h2>
          <div className="pills">
            <span className={`pill ${row.estado.toLowerCase()}`}>{row.estado}</span>
            <span className="pill neutral">{row.moneda}</span>
            <span className="pill neutral">Creada: {new Date(row.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="card">
          <h4>Datos del Cliente</h4>
          <div className="grid">
            <div><b>Nombre</b><div>{nombre || '—'}</div></div>
            <div><b>Usuario</b><div>{panel.usuario || row.cliente_info?.user_info?.username || '—'}</div></div>
            <div><b>Email</b><div>{email || '—'}</div></div>
            <div><b>Documento</b><div>{doc || '—'}</div></div>
            <div><b>Teléfono</b><div>{panel.telefono ?? row.cliente_info?.telefono ?? '—'}</div></div>
            <div><b>Dirección</b><div>{panel.direccion ?? row.cliente_info?.direccion ?? '—'}</div></div>
            <div><b>Ocupación</b><div>{panel.ocupacion ?? row.cliente_info?.ocupacion ?? '—'}</div></div>
            <div><b>Ingresos</b><div>
              {panel.ingresos != null
                ? Number(panel.ingresos).toLocaleString()
                : (row.cliente_info?.ingresos_mensuales != null
                    ? Number(row.cliente_info.ingresos_mensuales).toLocaleString()
                    : '—')}
            </div></div>
            <div><b>Puntaje</b><div>{panel.puntaje ?? row.cliente_info?.puntuacion_crediticia ?? '—'}</div></div>
            <div><b>Preferencial</b><div>{(panel.preferencial ?? row.cliente_info?.es_cliente_preferencial) ? 'Sí' : 'No'}</div></div>
          </div>
        </div>
      </div>

      <div className="section">
        <div className="card kpis">
          <div>
            <div className="k">Monto</div>
            <div className="v">{row.moneda} {Number(row.monto).toFixed(2)}</div>
          </div>
          <div>
            <div className="k">Plazo</div>
            <div className="v">{row.plazo_meses} meses</div>
          </div>
          <div>
            <div className="k">TNA</div>
            <div className="v">{row.tasa_nominal_anual}%</div>
          </div>
        </div>

        {/* Acciones */}
        <div className="panel">
          <h4>Evaluar (CU13)</h4>
          <input placeholder="score_riesgo (ej. 72.5)" value={score} onChange={(e) => setScore(e.target.value)} />
          <input placeholder="observación" value={obs} onChange={(e) => setObs(e.target.value)} />
          <button onClick={doEvaluar}>Guardar evaluación</button>
          {errEval && <pre className="err">{errEval}</pre>}
        </div>

        <div className="panel">
          <h4>Decidir (CU14)</h4>
          <button onClick={() => doDecidir('APROBAR')}>Aprobar</button>
          <button onClick={() => doDecidir('RECHAZAR')} style={{ background: '#dc3545' }}>Rechazar</button>
          {errDec && <pre className="err">{errDec}</pre>}
        </div>

        <div className="panel">
          <h4>Plan de pago (CU15)</h4>
          <Link className="btn" to={`/solicitudes/${id}/plan`}>Abrir plan</Link>
        </div>

        <div className="panel">
          <h4>Documentación (CU19/CU13)</h4>
          <Link className="btn" to={`/solicitudes/${id}/checklist`}>Abrir checklist</Link>
        </div>

        <div className="panel">
          <h4>Seguimiento (CU16)</h4>
          <Link className="btn" to={`/solicitudes/${id}/seguimiento`}>Ver seguimiento</Link>
        </div>
      </div>

      <style>{`
        .wrap { display:grid; gap:16px; }
        .header { display:flex; gap:16px; align-items:flex-start; justify-content:space-between; }
        .mono { font-family: monospace; font-size: .9em; }
        .pills { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
        .pill { padding:4px 8px; border-radius:999px; font-size:.85em; }
        .pill.neutral { background:#eef1f4; color:#334155; }
        .pill.aprobada { background:#d1fae5; color:#065f46; }
        .pill.rechazada { background:#fee2e2; color:#991b1b; }
        .pill.evaluada { background:#fff7ed; color:#9a3412; }
        .pill.enviada { background:#e0e7ff; color:#3730a3; }
        .card { background:#fff; padding:16px; border-radius:12px; }
        .grid { 
        display:grid; 
        grid-template-columns:repeat(2, minmax(220px, 1fr)); 
        gap:12px 24px; 
        }
        .grid > div > div {
          min-width: 0;
          overflow-wrap: anywhere;   /* permite cortar en cualquier punto si hace falta */
          word-break: break-word;    /* por si hay palabras largas sin espacios */
          line-height: 1.25;         /* un poco más de aire vertical */
        }

        .grid b { display:block; color:#64748b; font-weight:600; font-size:.85rem; }
        .section { display:grid; gap:12px; }
        .panel { background:#fff; padding:12px; border-radius:8px; display:grid; gap:8px; }
        .panel input { padding:8px; border:1px solid #ddd; border-radius:6px; }
        .panel button { background:#0d6efd; color:#fff; border:none; border-radius:6px; padding:8px 10px; }
        .btn { background:#198754;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none; }
        .err { color:crimson; white-space:pre-wrap; }
        .kpis { display:grid; grid-template-columns: repeat(3, minmax(160px, 1fr)); gap:12px; }
        .k { color:#64748b; font-size:.85rem; }
        .v { font-size:1.15rem; font-weight:700; }
        @media (max-width: 900px) {
          .header { flex-direction:column; }
          .grid { grid-template-columns: 1fr; }
          .kpis { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}
