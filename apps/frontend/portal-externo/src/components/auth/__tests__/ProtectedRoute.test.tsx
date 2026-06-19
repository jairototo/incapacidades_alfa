import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useAuthStore } from '@/store/authStore';

const Protected = () => <div>SECRETO</div>;
const renderAt = () => render(
  <MemoryRouter initialEntries={['/']}>
    <Routes>
      <Route path="/login" element={<div>LOGIN</div>} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Protected />} />
      </Route>
    </Routes>
  </MemoryRouter>,
);

describe('ProtectedRoute', () => {
  beforeEach(() => useAuthStore.getState().logout());

  it('redirects unauthenticated users to /login', () => {
    renderAt();
    expect(screen.getByText('LOGIN')).toBeInTheDocument();
  });

  it('shows access denied for authenticated non-EMPRESA', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { id: '1', username: 'a', email: 'a', nombre_completo: 'A', rol: 'AUDITOR', estado: 'ACTIVO', empresa_id: null, created_at: 'x' } as any });
    renderAt();
    expect(screen.getByText(/no tiene acceso/i)).toBeInTheDocument();
  });

  it('renders children for EMPRESA with empresa_id', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { id: '1', username: 'e', email: 'e', nombre_completo: 'E', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1', created_at: 'x' } as any });
    renderAt();
    expect(screen.getByText('SECRETO')).toBeInTheDocument();
  });

  it('logout button clears auth and redirects to /login', () => {
    useAuthStore.setState({ isAuthenticated: true, user: { id: '1', username: 'a', email: 'a', nombre_completo: 'A', rol: 'AUDITOR', estado: 'ACTIVO', empresa_id: null, created_at: 'x' } as any });

    const original = window.location;
    Object.defineProperty(window, 'location', { writable: true, value: { href: '' } });

    renderAt();
    fireEvent.click(screen.getByRole('button', { name: /volver al inicio de sesión/i }));

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(window.location.href).toBe('/login');

    // restore
    Object.defineProperty(window, 'location', { writable: true, value: original });
  });
});
