// src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';

import Login from './components/Login/Login';
import Logout from './components/Logout/Logout';
import PasswordReset from './components/PasswordReset/PasswordReset';
import UserManagement from './components/UserManagement/UserManagement';
import RoleManagement from './components/RoleManagement/RoleManagement';
import Dashboard from './components/Dashboard/Dashboard';
import ClientManagement from './components/ClientManagement/ClientManagement';
import EmployeeManagement from './components/EmployeeManagement/EmployeeManagement';

import Layout from './components/Layout/Layout';
import AuthLayout from './components/Auth/AuthLayout';

import './App.css';

// 👇 importa las páginas de Solicitudes
import SolicitudesList from './pages/solicitudes/SolicitudesList';
import SolicitudCreate from './pages/solicitudes/SolicitudCreate';
import SolicitudDetail from './pages/solicitudes/SolicitudDetail';
import PlanView from './pages/solicitudes/PlanView';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      verifyToken();
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async () => {
    try {
      await axios.get('http://localhost:8000/api/users/');
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Token verification failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete axios.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = () => setIsAuthenticated(true);
  const handleLogoutSuccess = () => { setIsAuthenticated(false); setUserRole(null); };

  if (loading) return <div className="loading">Cargando...</div>;

  const AppRoutes = () => {
    const location = useLocation();
    const isAuthPage = location.pathname === "/login" || location.pathname === "/password-reset";

    return (
      <div className="App">
        {!isAuthPage && (
          <header className="App-header">
            <h1>Gestión de Solicitudes de Crédito</h1>
          </header>
        )}

        <main className="App-main">
          <Routes>
            {/* Raíz -> redirige según sesión (opcional: a /solicitudes) */}
            <Route
              path="/"
              element={
                isAuthenticated
                  ? <Navigate to="/solicitudes" replace />
                  : <Navigate to="/login" replace />
              }
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

            {/* Protegidas */}
            {isAuthenticated && (
              <>
                <Route
                  path="/dashboard"
                  element={
                    <Layout>
                      <Dashboard />
                    </Layout>
                  }
                />

                <Route
                  path="/users"
                  element={
                    <Layout>
                      <UserManagement />
                    </Layout>
                  }
                />
                <Route
                  path="/roles"
                  element={
                    <Layout>
                      <RoleManagement />
                    </Layout>
                  }
                />
                <Route
                  path="/clientes"
                  element={
                    <Layout>
                      <ClientManagement />
                    </Layout>
                  }
                />
                <Route
                  path="/empleados"
                  element={
                    <Layout>
                      <EmployeeManagement />
                    </Layout>
                  }
                />

                {/* 👇 NUEVAS RUTAS DE SOLICITUDES */}
                <Route
                  path="/solicitudes"
                  element={
                    <Layout>
                      <SolicitudesList />
                    </Layout>
                  }
                />
                <Route
                  path="/solicitudes/nueva"
                  element={
                    <Layout>
                      <SolicitudCreate />
                    </Layout>
                  }
                />
                <Route
                  path="/solicitudes/:id"
                  element={
                    <Layout>
                      <SolicitudDetail />
                    </Layout>
                  }
                />
                <Route
                  path="/solicitudes/:id/plan"
                  element={
                    <Layout>
                      <PlanView />
                    </Layout>
                  }
                />

                {/* 404 protegido */}
                <Route
                  path="*"
                  element={
                    <Layout>
                      <div style={{ padding: 24 }}>
                        <h2>Página no encontrada</h2>
                        <p>Usa el menú de la izquierda para navegar.</p>
                      </div>
                    </Layout>
                  }
                />
              </>
            )}
          </Routes>
        </main>

        {isAuthenticated && (
          <footer className="App-footer">
            <p>&copy; {new Date().getFullYear()} Sistema de Gestión de Créditos</p>
          </footer>
        )}
      </div>
    );
  };

  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App;
