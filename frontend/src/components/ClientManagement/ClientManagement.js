// src/components/ClientManagement/ClientManagement.js
import React, { useEffect, useMemo, useState } from 'react';
import api from '../../api/http';
import './ClientManagement.css';

export default function ClientManagement() {
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const [filters, setFilters] = useState({
    q: '',
    tipo_documento: '',
    preferencial: '',
  });

  useEffect(() => {
    const load = async () => {
      setBusy(true); setErr('');
      try {
        const { data } = await api.get('/users/');
        // data es array con campos + cliente_info / empleado_info
        const onlyClients = (Array.isArray(data) ? data : data?.results || [])
          .filter(u => !!u.cliente_info);
        setRows(onlyClients);
      } catch (e) {
        console.error('Fetch clients error:', e);
        setErr('Error al cargar los clientes');
        setRows([]);
      } finally {
        setBusy(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = filters.q.toLowerCase().trim();
    return rows.filter(u => {
      const c = u.cliente_info || {};
      const matchQ =
        u.username?.toLowerCase().includes(q) ||
        u.first_name?.toLowerCase().includes(q) ||
        u.last_name?.toLowerCase().includes(q) ||
        (c.documento || '').toLowerCase().includes(q);

      const tipo = (c.documento || '').split(' ')[0]; // p.ej. "CI 1234"
      const matchTipo = !filters.tipo_documento || tipo === filters.tipo_documento;

      const pref = c.preferencial === true; // viene como booleano
      const matchPref =
        filters.preferencial === '' ||
        (filters.preferencial === 'true' && pref) ||
        (filters.preferencial === 'false' && !pref);

      return matchQ && matchTipo && matchPref;
    });
  }, [rows, filters]);

  if (busy) return <div className="loading">Cargando clientes…</div>;

  return (
    <div className="client-management-container">
      <h2>Gestión de Clientes</h2>

      {err && <div className="error-message">{err}</div>}

      <div className="filters">
        <input
          type="text"
          name="q"
          placeholder="Buscar por nombre, usuario o documento"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className="search-input"
        />

        <select
          name="tipo_documento"
          value={filters.tipo_documento}
          onChange={(e) => setFilters({ ...filters, tipo_documento: e.target.value })}
        >
          <option value="">Todos los documentos</option>
          <option value="CI">Cédula de Identidad</option>
          <option value="PAS">Pasaporte</option>
          <option value="NIT">NIT</option>
        </select>

        <select
          name="preferencial"
          value={filters.preferencial}
          onChange={(e) => setFilters({ ...filters, preferencial: e.target.value })}
        >
          <option value="">Todos</option>
          <option value="true">Preferenciales</option>
          <option value="false">Regulares</option>
        </select>
      </div>

      <div className="clients-list">
        <h3>Lista de Clientes</h3>
        {filtered.length === 0 ? (
          <p>No hay clientes registrados.</p>
        ) : (
          <table className="clients-table">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Email</th>
                <th>Documento</th>
                <th>Teléfono</th>
                <th>Ingresos</th>
                <th>Preferencial</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(u => {
                const c = u.cliente_info || {};
                return (
                  <tr key={u.id}>
                    <td>{u.username}</td>
                    <td>{`${u.first_name || ''} ${u.last_name || ''}`.trim() || '—'}</td>
                    <td>{u.email}</td>
                    <td>{c.documento || '—'}</td>
                    <td>{c.telefono || '—'}</td>
                    <td>{c.ingresos ?? '—'}</td>
                    <td>
                      <span className={`client-type ${c.preferencial ? 'preferential' : 'regular'}`}>
                        {c.preferencial ? 'Sí' : 'No'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
