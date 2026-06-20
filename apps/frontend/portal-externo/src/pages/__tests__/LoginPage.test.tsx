import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { authService } from '@/services/authService';

vi.mock('@/services/authService');

const mockLogin = vi.fn();
const mockNavigate = vi.fn();

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: any) => any) => selector({ login: mockLogin }),
}));

vi.mock('react-router-dom', async (orig) => ({
  ...(await orig() as any),
  useNavigate: () => mockNavigate,
}));

const renderPage = () => render(<MemoryRouter><LoginPage /></MemoryRouter>);

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockClear();
    mockNavigate.mockClear();
  });

  it('shows validation errors on empty submit', async () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/el usuario es obligatorio/i)).toBeInTheDocument();
  });

  it('blocks non-EMPRESA users with an access message', async () => {
    (authService.login as any).mockResolvedValue({
      access_token: 'a', refresh_token: 'r', token_type: 'bearer', expires_in: 900,
      user: { id: '1', username: 'aud', email: 'a@a.com', nombre_completo: 'Aud', rol: 'AUDITOR', estado: 'ACTIVO', empresa_id: null, created_at: 'x' },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText(/usuario/i), { target: { value: 'aud' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'secret12' } });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    expect(await screen.findByText(/no tiene acceso a este portal/i)).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('stores session and navigates to / on successful EMPRESA login', async () => {
    (authService.login as any).mockResolvedValue({
      access_token: 'tok', refresh_token: 'ref', token_type: 'bearer', expires_in: 900,
      user: { id: '1', username: 'emp', email: 'e@e.com', nombre_completo: 'Emp', rol: 'EMPRESA', estado: 'ACTIVO', empresa_id: 'co-1', created_at: 'x' },
    });
    renderPage();
    fireEvent.change(screen.getByLabelText(/usuario/i), { target: { value: 'emp' } });
    fireEvent.change(screen.getByLabelText(/contraseña/i), { target: { value: 'pass1234' } });
    fireEvent.click(screen.getByRole('button', { name: /ingresar/i }));
    await waitFor(() => expect(mockLogin).toHaveBeenCalledOnce());
    expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
  });
});
