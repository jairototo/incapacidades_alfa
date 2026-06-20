import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import { useAuthStore } from '@/store/authStore';

describe('Dashboard', () => {
  beforeEach(() => useAuthStore.setState({
    isAuthenticated: true,
    user: { id: '1', username: 'e', email: 'e', nombre_completo: 'Empresa Uno', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1', empresa: { id: 'emp-1', nit: '900', razon_social: 'ACME S.A.', estado: 'ACTIVA' }, created_at: 'x' } as any,
  }));

  it('greets the company and shows the three actions', () => {
    render(<MemoryRouter><Dashboard /></MemoryRouter>);
    expect(screen.getByText(/ACME S\.A\./)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /radicación individual/i })).toHaveAttribute('href', '/radicar/individual');
    expect(screen.getByRole('link', { name: /radicación masiva/i })).toHaveAttribute('href', '/radicar/masiva');
    expect(screen.getByRole('link', { name: /consulta/i })).toHaveAttribute('href', '/consulta');
  });
});
