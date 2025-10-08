import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Login from './components/Login/Login';

// Páginas de solicitudes
import SolicitudesList from './pages/solicitudes/SolicitudesList';
import SolicitudCreate from './pages/solicitudes/SolicitudCreate';
import SolicitudDetail from './pages/solicitudes/SolicitudDetail';
import PlanView from './pages/solicitudes/PlanView';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access_token');
  const loc = useLocation();
  if (!token) return <Navigate to="/login" replace state={{ from: loc }} />;
  return children;
}

export default function App() {
  return (
    <Routes>
      {/* Pública */}
      <Route path="/login" element={<Login onLoginSuccess={() => window.location.replace('/')} />} />

      {/* Protegida */}
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <Layout>
              <Routes>
                {/* 👇 IMPORTANTE: aquí sí existen estas rutas */}
                <Route path="/" element={<Navigate to="/solicitudes" replace />} />
                <Route path="/solicitudes" element={<SolicitudesList />} />
                <Route path="/solicitudes/nueva" element={<SolicitudCreate />} />
                <Route path="/solicitudes/:id" element={<SolicitudDetail />} />
                <Route path="/solicitudes/:id/plan" element={<PlanView />} />
                <Route path="*" element={<div>404</div>} />
              </Routes>
            </Layout>
          </PrivateRoute>
        }
      />
    </Routes>
  );
}
