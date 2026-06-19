import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { authService } from '@/services/authService';

vi.mock('@/services/authService');
const renderPage = () => render(<MemoryRouter><LoginPage /></MemoryRouter>);

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks());

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
  });
});
