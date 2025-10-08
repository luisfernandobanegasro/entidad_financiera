// src/services/plan.js
import api from '../config/axios';

/** GET /api/solicitudes/:id/plan-pagos/ */
export async function getPlan(solicitudId) {
  const { data } = await api.get(`/api/solicitudes/${solicitudId}/plan-pagos/`);
  return data;
}

/** POST /api/solicitudes/:id/plan-pagos/generar?overwrite=... */
export async function generarPlan(solicitudId, { overwrite = false } = {}) {
  const qs = overwrite ? '?overwrite=true' : '';
  const { data } = await api.post(`/api/solicitudes/${solicitudId}/plan-pagos/generar${qs}`);
  return data; // { plan_id: "..." }
}

/** URL absoluta para exportar (PDF o XLSX) */
export function getPlanExportUrl(solicitudId, format = 'pdf') {
  const base = api.defaults.baseURL || (import.meta.env?.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000');
  return `${base}/api/solicitudes/${solicitudId}/plan-pagos/export?format=${format}`;
}
