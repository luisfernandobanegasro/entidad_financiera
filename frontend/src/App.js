// src/App.js
import React, { useState, useEffect } from 'react';
// Nota: mantenemos BrowserRouter como Router aquí (Opción B). 
// Si luego prefieres Opción A, moverás el Router a index.js.
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';

// Páginas / componentes
import Login from './components/Login/Login';
import Logout from './components/Logout/Logout';
import PasswordReset from './components/PasswordReset/PasswordReset';
import UserManagement from './components/UserManagement/UserManagement';
import RoleManagement from './components/RoleManagement/RoleManagement';
import Dashboard from './components/Dashboard/Dashboard';
import ClientManagement from './components/ClientManagement/ClientManagement';
import EmployeeManagement from './components/EmployeeManagement/EmployeeManagement';

// Layouts
import Layout from './components/Layout/Layout';         // Sidebar + Main para rutas protegidas
import AuthLayout from './components/Auth/AuthLayout';   // Fullscreen centrado para login/reset

import './App.css';

function App() {
  // ======= Estado de autenticación global =======
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null); // por si lo usas luego
  const [loading, setLoading] = useState(true);


  // ======= Verificar token al inicio =======
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
      // Usamos un endpoint que requiere auth para validar el token
      await axios.get('http://localhost:8000/api/users/');
      setIsAuthenticated(true);
      // Si necesitas el rol:
      // setUserRole( ... );
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

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    // aquí podrías volver a cargar datos del usuario/rol
  };

  const handleLogoutSuccess = () => {
    setIsAuthenticated(false);
    setUserRole(null);
  };

  if (loading) {
    return <div className="loading">Cargando...</div>;
  }

  // ===========================================================
  // OJO: useLocation() NO puede usarse aquí arriba del Router.
  // Solución (Opción B): creamos un componente interno "AppRoutes"
  // que SÍ se renderiza DENTRO del <Router>.
  // ===========================================================
  const AppRoutes = () => {
    const location = useLocation();
    const isAuthPage = location.pathname === "/login" || location.pathname === "/password-reset";
    
    return (
      <div className="App">
        {/* Header: solo se muestra si NO estamos en rutas de auth */}
        {!isAuthPage && (
          <header className="App-header">
            <h1>Sistema de Gestión de Solicitudes de Crédito</h1>
            {/* {isAuthenticated && (
              <div className="header-actions">
                <Logout onLogoutSuccess={handleLogoutSuccess} />
              </div>
            )} */}
          </header>
        )}

        <main className="App-main">
          <Routes>
            {/* Ruta raíz: redirige según autenticación */}
            <Route 
              path="/"
              element={
                isAuthenticated
                  ? <Navigate to="/dashboard" replace />
                  : <Navigate to="/login" replace />
              }
            />

            {/* Login: fullscreen centrado, sin header/footer */}
            <Route
              path="/login"
              element={
                isAuthenticated
                  ? <Navigate to="/dashboard" replace />
                  : (
                    <AuthLayout>
                      <Login onLoginSuccess={handleLoginSuccess} />
                    </AuthLayout>
                  )
              }
            />

            {/* Password Reset: fullscreen centrado, sin header/footer */}
            <Route
              path="/password-reset"
              element={
                isAuthenticated
                  ? <Navigate to="/dashboard" replace />
                  : (
                    <AuthLayout>
                      <PasswordReset />
                    </AuthLayout>
                  )
              }
            />

            {/* ===== Rutas protegidas (todas envueltas en Layout con sidebar) ===== */}
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
                  
                
                 {/* 404 */}
                <Route
                  path="*"
                  element={
                    <Layout>
                      <div style={{padding: 24}}>
                        <h2>Página no encontrada</h2>
                        <p>Esta vista aún no está implementada. Usa el menú de la izquierda para navegar.</p>
                      </div>
                    </Layout>
                  }
                />
              </>
            )}
           </Routes>
        </main>

        {/* Footer: solo si hay sesión (por lo tanto nunca en login/reset) */}
        {isAuthenticated && (
          <footer className="App-footer">
            <p>&copy; {new Date().getFullYear()} Sistema de Gestión de Créditos - Grupo 10</p>
          </footer>
        )}
      </div>
    );
  };

  // Aquí sí existe <Router>, y DENTRO renderizamos AppRoutes (que usa useLocation)
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App;
