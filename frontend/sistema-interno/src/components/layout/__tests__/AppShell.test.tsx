import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AppShell } from '../AppShell';
import * as authStoreModule from '@/store/authStore';
import { RolUsuario, EstadoUsuario, type Usuario } from '@/types/auth';

/**
 * Tests para el componente AppShell
 */

// Mock del authStore
vi.mock('@/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

// Mock de react-router-dom Outlet
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Outlet: () => <div data-testid="outlet-content">Outlet Content</div>,
  };
});

const mockUser: Usuario = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  username: 'admin',
  email: 'admin@test.com',
  nombres: 'Admin',
  apellidos: 'Test',
  rol: RolUsuario.ADMIN,
  estado: EstadoUsuario.ACTIVO,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('AppShell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock authStore con usuario por defecto
    vi.spyOn(authStoreModule, 'useAuthStore').mockReturnValue({
      isAuthenticated: true,
      user: mockUser,
      accessToken: 'token123',
      refreshToken: 'refresh123',
      login: vi.fn(),
      logout: vi.fn(),
      refreshAccessToken: vi.fn(),
    });
  });

  it('debe renderizar el layout completo', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    // Verificar que renderiza los componentes principales
    expect(screen.getAllByText('Incapacidades').length).toBeGreaterThan(0); // Logo en Sidebar + menú
    expect(screen.getByRole('heading', { name: /Sistema de Gestión de Incapacidades/i })).toBeInTheDocument(); // Header
    expect(screen.getByText(/© 2026/i)).toBeInTheDocument(); // Footer
    expect(screen.getByTestId('outlet-content')).toBeInTheDocument(); // Outlet
  });

  it('debe renderizar el Sidebar con el usuario actual', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    // Verificar que muestra el usuario en el Sidebar
    expect(screen.getByText('Admin Test')).toBeInTheDocument();
    expect(screen.getAllByText('ADMIN').length).toBeGreaterThan(0); // Aparece en badge y sidebar
  });

  it('debe renderizar el menú de navegación', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    // Verificar ítems de menú
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getAllByText('Incapacidades').length).toBeGreaterThan(0);
    expect(screen.getByText('Órdenes de Pago')).toBeInTheDocument();
    expect(screen.getByText('Usuarios')).toBeInTheDocument();
  });

  it('debe renderizar el Header con badge de rol', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    // Verificar badge de rol en Header (aparece 2 veces: header y sidebar)
    const adminBadges = screen.getAllByText('ADMIN');
    expect(adminBadges.length).toBeGreaterThan(0);
  });

  it('debe renderizar el Footer con copyright', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    expect(screen.getByText(/© 2026 Sistema de Gestión de Incapacidades/i)).toBeInTheDocument();
    expect(screen.getByText(/Versión 1.0.0/i)).toBeInTheDocument();
  });

  it('debe renderizar el Outlet para contenido de rutas', () => {
    render(
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    );

    expect(screen.getByTestId('outlet-content')).toBeInTheDocument();
    expect(screen.getByText('Outlet Content')).toBeInTheDocument();
  });
});
