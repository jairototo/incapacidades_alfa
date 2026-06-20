import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';

const mockLogout = vi.fn();
const mockNavigate = vi.fn();

const baseUser = {
  id: '1', username: 'emp', email: 'rrhh@acme.com', nombre_completo: 'Empresa Uno',
  rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'emp-1',
  empresa: { id: 'emp-1', nit: '900', razon_social: 'ACME S.A.', estado: 'ACTIVA' },
  created_at: 'x',
};

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: any) => any) => selector({ user: baseUser, logout: mockLogout }),
}));

vi.mock('react-router-dom', async (orig) => ({
  ...(await (orig() as any)),
  useNavigate: () => mockNavigate,
}));

const renderNavbar = () => render(<MemoryRouter><Navbar /></MemoryRouter>);

describe('Navbar', () => {
  beforeEach(() => {
    mockLogout.mockClear();
    mockNavigate.mockClear();
  });

  it('renders the logo, portal name and the three nav links', () => {
    renderNavbar();
    expect(screen.getByAltText(/seguros alfa/i)).toBeInTheDocument();
    expect(screen.getByText(/portal empresas/i)).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /radicación individual/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: /radicación masiva/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole('link', { name: /consulta/i }).length).toBeGreaterThan(0);
  });

  it('opens the user menu showing company + contact, and logs out', () => {
    renderNavbar();
    // menu closed initially
    expect(screen.queryByText(/cerrar sesión/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /menú de usuario/i }));
    expect(screen.getByText('ACME S.A.')).toBeInTheDocument();
    expect(screen.getByText('rrhh@acme.com')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('menuitem', { name: /cerrar sesión/i }));
    expect(mockLogout).toHaveBeenCalledOnce();
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('toggles the mobile menu', () => {
    renderNavbar();
    const toggle = screen.getByRole('button', { name: /abrir menú/i });
    fireEvent.click(toggle);
    // after opening, the close affordance is present
    expect(screen.getByRole('button', { name: /cerrar menú/i })).toBeInTheDocument();
  });
});
