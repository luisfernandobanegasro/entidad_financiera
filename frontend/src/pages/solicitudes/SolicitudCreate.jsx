import React, { useEffect, useState } from 'react';
import { fetchClientes } from '../../services/clientes';
import { createSolicitud } from '../../services/solicitudes';
import { useNavigate } from 'react-router-dom';

export default function SolicitudCreate() {
  const nav = useNavigate();
  const [clientes, setClientes] = useState([]);
  const [loadingClientes, setLoadingClientes] = useState(true);
  const [errCli, setErrCli] = useState('');

  const [form, setForm] = useState({
    cliente: '',
    monto: '',
    plazo_meses: '',
    tasa_nominal_anual: '24.0',
    moneda: 'BOB',
  });
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoadingClientes(true);
        const data = await fetchClientes(); // devuelve array con id
        if (!mounted) return;
        setClientes(data);
      } catch (e) {
        setErrCli('No se pudieron cargar clientes');
      } finally {
        setLoadingClientes(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const handle = e => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        cliente: Number(form.cliente),
        monto: Number(form.monto),
        plazo_meses: Number(form.plazo_meses),
        tasa_nominal_anual: Number(form.tasa_nominal_anual),
      };
      const created = await createSolicitud(payload);
      nav(`/solicitudes/${created.id}`);
    } catch (e) {
      setErr(JSON.stringify(e.response?.data || 'Error', null, 2));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{maxWidth:560}}>
      <h2>Nueva Solicitud (interno)</h2>
      <form onSubmit={submit} className="form-grid">
        <label>Cliente</label>
        {loadingClientes ? (
          <div>Cargando clientes…</div>
        ) : (
          <select name="cliente" value={form.cliente} onChange={handle} required>
            <option value="">-- Selecciona --</option>
            {clientes.map(c => (
              <option key={c.id} value={c.id}>
                {c.user_info?.first_name} {c.user_info?.last_name} — #{c.id}
              </option>
            ))}
          </select>
        )}
        {errCli && <div style={{color:'crimson'}}>{errCli}</div>}

        <label>Monto</label>
        <input name="monto" value={form.monto} onChange={handle} required />

        <label>Plazo (meses)</label>
        <input name="plazo_meses" value={form.plazo_meses} onChange={handle} required />

        <label>Tasa nominal anual (%)</label>
        <input name="tasa_nominal_anual" value={form.tasa_nominal_anual} onChange={handle} />

        <label>Moneda</label>
        <input name="moneda" value={form.moneda} onChange={handle} />

        <div style={{display:'flex',gap:8,marginTop:10}}>
          <button className="btn" disabled={submitting}>Crear</button>
        </div>

        {err && <pre style={{color:'crimson',whiteSpace:'pre-wrap'}}>{err}</pre>}
      </form>

      <style>{`
        .form-grid { display:grid; gap:8px; background:#fff; padding:16px; border-radius:8px; }
        .form-grid input, .form-grid select { padding:8px; border:1px solid #ddd; border-radius:6px; }
        .btn { background:#198754;color:#fff;padding:8px 12px;border-radius:6px;border:none; }
      `}</style>
    </div>
  );
}
