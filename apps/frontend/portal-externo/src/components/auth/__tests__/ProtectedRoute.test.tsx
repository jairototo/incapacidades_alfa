import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
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
});
