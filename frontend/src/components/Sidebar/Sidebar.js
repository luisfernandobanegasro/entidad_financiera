// src/components/Sidebar/Sidebar.js
import React, { useState, useEffect } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import axios from "../../config/axios";
import "./Sidebar.css";
import Swal from "sweetalert2";
/**
 * Sidebar izquierdo colapsable.
 * - Usa NavLink para resaltar ruta activa.
 * - Colapsa a iconos (64px); expandido 240px.
 * - Sincroniza su estado con <html data-sidebar="..."> para que el header se adapte.
 */
export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  // 🔄 Sincroniza el estado del sidebar con el atributo en <html>
  //    Tu App.css usa este atributo para ajustar el header dinámicamente.
  useEffect(() => {
    document.documentElement.setAttribute(
      "data-sidebar",
      collapsed ? "collapsed" : "expanded"
    );
  }, [collapsed]);

  // ⛔ Cerrar sesión: limpia tokens, limpia axios y redirige a /login
  const handleLogout = async (e) => {
  e.preventDefault(); // evita navegar al href antes del modal

  const result = await Swal.fire({
    title: '¿Cerrar sesión?',
    text: 'Tu sesión actual se cerrará y deberás volver a iniciar sesión.',
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Sí, cerrar sesión',
    cancelButtonText: 'Cancelar',
    confirmButtonColor: '#20c997',
    cancelButtonColor: '#6c757d',
    reverseButtons: true
  });

  if (!result.isConfirmed) return;

  try {
    // await axios.post('http://localhost:8000/api/auth/logout/', {});
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete axios.defaults.headers.common['Authorization'];

    await Swal.fire({
      title: 'Sesión cerrada',
      icon: 'success',
      timer: 1200,
      showConfirmButton: false
    });

    window.location.href = '/login';
  }
};

  return (
    <aside
      className={`sidebar ${collapsed ? "collapsed" : ""}`}
      aria-label="Menú lateral"
    >
      <div className="sidebar__header">
        <button
          className="sidebar__toggle"
          onClick={() => setCollapsed((v) => !v)}
          aria-label={collapsed ? "Expandir menú" : "Colapsar menú"}
          title={collapsed ? "Expandir" : "Colapsar"}
        >
          ☰
        </button>
        {!collapsed && <span className="sidebar__brand">MiApp</span>}
      </div>

      <nav className="sidebar__nav">
        <NavLink to="/" end className="sidebar__link">
          <span className="sidebar__icon">🏠</span>
          {!collapsed && <span>Dashboard</span>}
        </NavLink>

        <NavLink to="/users" className="sidebar__link">
          <span className="sidebar__icon">👥</span>
          {!collapsed && <span>Usuarios</span>}
        </NavLink>

        <NavLink to="/clientes" className="sidebar__link">
          <span className="sidebar__icon">🧾</span>
          {!collapsed && <span>Clientes</span>}
        </NavLink>

        <NavLink to="/empleados" className="sidebar__link">
          <span className="sidebar__icon">🧑‍💼</span>
          {!collapsed && <span>Empleados</span>}
        </NavLink>

        <NavLink to="/roles" className="sidebar__link">
          <span className="sidebar__icon">🛡️</span>
          {!collapsed && <span>Roles y Permisos</span>}
        </NavLink>

        <NavLink to="/solicitudes" className="sidebar__link">
          <span className="sidebar__icon">📄</span>
          {!collapsed && <span>Solicitudes</span>}
        </NavLink>

        <NavLink to="/solicitudes/nueva" className="sidebar__link">
          <span className="sidebar__icon">➕</span>
          {!collapsed && <span>Nueva solicitud</span>}
        </NavLink>
        <NavLink to="/simulador" className="sidebar__link">
          <span className="sidebar__icon">🧮</span>
          {!collapsed && <span>Simulador</span>}
        </NavLink>
        
        <NavLink to="/productos/requisitos" className="sidebar__link">
          <span className="sidebar__icon">🧩</span>
          {!collapsed && <span>Editor de requisitos</span>}
        </NavLink>

        {/* Cerrar sesión desde el menú lateral */}
        <a
          href="/logout"
          onClick={handleLogout}
          className="sidebar__link sidebar__link--danger"
        >
          <span className="sidebar__icon">🚪</span>
          {!collapsed && <span>Cerrar sesión</span>}
        </a>
      </nav>

      {!collapsed && (
        <div className="sidebar__footer">
          <small>© {new Date().getFullYear()} Gestión de Créditos</small>
        </div>
      )}
    </aside>
  );
}
