// src/App.js
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import api, { setTokenPair, clearTokenPair } from './config/axios';

// Layouts
import Layout from './components/Layout/Layout';
import AuthLayout from './components/Auth/AuthLayout';
import RequireAuth from './components/Auth/RequireAuth';

// Auth
import Login from './components/Login/Login';
import PasswordReset from './components/PasswordReset/PasswordReset';

// Gestión (si las usas)
import Dashboard from './components/Dashboard/Dashboard';
import UserManagement from './components/UserManagement/UserManagement';
import RoleManagement from './components/RoleManagement/RoleManagement';
import ClientManagement from './components/ClientManagement/ClientManagement';
import EmployeeManagement from './components/EmployeeManagement/EmployeeManagement';

// Solicitudes
import SolicitudesList from './pages/solicitudes/SolicitudesList';
import SolicitudCreate from './pages/solicitudes/SolicitudCreate';
import SolicitudDetail from './pages/solicitudes/SolicitudDetail';
import SolicitudChecklist from './pages/solicitudes/SolicitudChecklist';
import PlanView from './pages/solicitudes/PlanView';
import Simulador from './pages/solicitudes/Simulador';

// Productos
import RequisitosEditor from './pages/productos/RequisitosEditor';

import './App.css';

function App() {
  const [authLoading, setAuthLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Verifica sesión al montar
  useEffect(() => {
    const verify = async () => {
      try {
        // Si no hay token, salimos rápido
        const token =
          localStorage.getItem('access_token') ||
          localStorage.getItem('access');
        if (!token) {
          setIsAuthenticated(false);
          return;
        }
        // Llama SIEMPRE a /api/users/me/
        await api.get('/users/me/');
        setIsAuthenticated(true);
      } catch (err) {
        // Limpia todo si falla
        clearTokenPair();
        setIsAuthenticated(false);
        // (opcional) console.warn('Verificación falló:', err);
      } finally {
        setAuthLoading(false);
      }
    };
    verify();
  }, []);

  const handleLoginSuccess = (tokens) => {
    // si tu login te entrega tokens, guárdalos
    if (tokens?.access || tokens?.refresh) {
      setTokenPair(tokens);
    }
    setIsAuthenticated(true);
  };

  return (
    <Router>
      <Routes>
        {/* Home */}
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/solicitudes" replace /> : <Navigate to="/login" replace />}
        />

        {/* Públicas */}
        <Route
          path="/login"
          element={
            isAuthenticated
              ? <Navigate to="/solicitudes" replace />
              : (
                <AuthLayout>
                  <Login onLoginSuccess={handleLoginSuccess} />
                </AuthLayout>
              )
          }
        />
        <Route
          path="/password-reset"
          element={
            isAuthenticated
              ? <Navigate to="/solicitudes" replace />
              : (
                <AuthLayout>
                  <PasswordReset />
                </AuthLayout>
              )
          }
        />

        {/* Protegidas (siempre registradas; se protegen con RequireAuth) */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><Dashboard /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/users"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><UserManagement /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/roles"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><RoleManagement /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/clientes"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><ClientManagement /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/empleados"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><EmployeeManagement /></Layout>
            </RequireAuth>
          }
        />

        {/* CU11 Simulador */}
        <Route
          path="/simulador"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><Simulador /></Layout>
            </RequireAuth>
          }
        />

        {/* Solicitudes */}
        <Route
          path="/solicitudes"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><SolicitudesList /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/solicitudes/nueva"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><SolicitudCreate /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/solicitudes/:id"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><SolicitudDetail /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/solicitudes/:id/checklist"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><SolicitudChecklist /></Layout>
            </RequireAuth>
          }
        />
        <Route
          path="/solicitudes/:id/plan"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><PlanView /></Layout>
            </RequireAuth>
          }
        />

        {/* Editor de requisitos */}
        <Route
          path="/productos/requisitos"
          element={
            <RequireAuth authed={isAuthenticated} loading={authLoading}>
              <Layout><RequisitosEditor /></Layout>
            </RequireAuth>
          }
        />

        {/* 404 */}
        <Route path="*" element={<div style={{ padding: 24 }}>Página no encontrada.</div>} />
      </Routes>
    </Router>
  );
}

export default App;
