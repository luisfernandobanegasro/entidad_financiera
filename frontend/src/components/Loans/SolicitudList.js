import React, { useEffect, useState } from 'react';
import axios from '../../config/axios';

export default function SolicitudList() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get('/api/solicitudes/', { withCredentials:true });
      setRows(data); setError('');
    } catch (e) { setError('No se pudieron cargar'); }
    finally { setLoading(false); }
  };
  useEffect(()=>{ load(); }, []);

  const evaluar = async (id) => {
    const score = prompt('Score de riesgo (0-100):', '70');
    const obs = prompt('Observación:', '');
    if (score == null) return;
    await axios.patch(`/api/solicitudes/${id}/evaluar/`, { score_riesgo: Number(score), observacion_evaluacion: obs }, { withCredentials:true });
    load();
  };
  const decidir = async (id, decision) => {
    await axios.post(`/api/solicitudes/${id}/decidir/`, { decision }, { withCredentials:true });
    load();
  };

  if (loading) return <div>Cargando…</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className="space-y-2">
      <table className="min-w-full text-sm">
        <thead><tr>
          <th>ID</th><th>Cliente</th><th>Monto</th><th>Plazo</th><th>Tasa</th><th>Estado</th><th>Acciones</th>
        </tr></thead>
        <tbody>
          {rows.map(r=>(
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.cliente_nombre}</td>
              <td>{r.monto}</td>
              <td>{r.plazo_meses}</td>
              <td>{r.tasa_nominal_anual}%</td>
              <td>{r.estado}</td>
              <td className="space-x-2">
                <button onClick={()=>evaluar(r.id)}>Evaluar</button>
                <button onClick={()=>decidir(r.id,'APROBAR')}>Aprobar</button>
                <button onClick={()=>decidir(r.id,'RECHAZAR')}>Rechazar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
