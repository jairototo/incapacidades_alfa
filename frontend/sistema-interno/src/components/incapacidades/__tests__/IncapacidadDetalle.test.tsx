import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IncapacidadDetalle } from '../IncapacidadDetalle';
import { EstadoIncapacidad, TipoIncapacidad } from '@/types';

const mockIncapacidadARL = {
  id: 'test-id-arl',
  numero: 'INC-2024-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  fecha_inicio: '2024-01-15',
  fecha_fin: '2024-01-20',
  dias_totales: 5,
  diagnostico_cie10: 'S06.0',
  diagnostico_descripcion: 'Conmoción cerebral',
  valor_total: 500000,
  valor_dia: 100000,
  observaciones: 'Observaciones de prueba',
  prioridad: 'ALTA',
  empleado: {
    id: 'emp-123',
    numero_documento: '12345678',
    tipo_documento: 'CEDULA',
    nombres: 'Juan Carlos',
    apellidos: 'Pérez Gómez',
    email: 'juan@example.com',
    telefono: '3001234567',
  },
  empresa: {
    id: 'emp-456',
    nit: '900123456',
    razon_social: 'Empresa Test SA',
    email_contacto: 'empresa@test.com',
  },
  siniestro: {
    id: 'sin-789',
    numero_siniestro: 'SIN-2024-001',
    fecha_ocurrencia: '2024-01-14',
    lugar_ocurrencia: 'Oficina principal',
    descripcion: 'Caída en escaleras',
  },
  created_at: '2024-01-10T10:00:00Z',
  updated_at: '2024-01-10T10:00:00Z',
};

const mockIncapacidadSalud = {
  id: 'test-id-salud',
  numero: 'INC-2024-002',
  tipo: TipoIncapacidad.SALUD,
  estado: EstadoIncapacidad.APROBADA,
  fecha_inicio: '2024-02-01',
  fecha_fin: '2024-02-05',
  dias_totales: 4,
  diagnostico_cie10: 'J18.9',
  diagnostico_descripcion: 'Neumonía',
  valor_total: 400000,
  valor_dia: 100000,
  observaciones: null,
  prioridad: 'NORMAL',
  afiliado: {
    id: 'afi-321',
    numero_documento: '87654321',
    tipo_documento: 'CEDULA',
    nombres: 'María',
    apellidos: 'López',
    email: 'maria@example.com',
    telefono: '3007654321',
    numero_afiliacion: 'POL-2024-001',
    estado: 'ACTIVO',
  },
  created_at: '2024-02-01T08:00:00Z',
  updated_at: '2024-02-01T08:00:00Z',
};

describe('IncapacidadDetalle', () => {
  it('debe renderizar los 8 cards de información', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Verificar que aparecen los títulos de las cards
    expect(screen.getByText('Información General')).toBeInTheDocument();
    expect(screen.getByText('Paciente')).toBeInTheDocument();
    expect(screen.getByText('Empresa')).toBeInTheDocument();
    expect(screen.getByText('Diagnóstico')).toBeInTheDocument();
    expect(screen.getByText('Fechas')).toBeInTheDocument();
    expect(screen.getByText('Valores')).toBeInTheDocument();
    expect(screen.getByText('Siniestro Asociado')).toBeInTheDocument();
    expect(screen.getByText('Metadatos')).toBeInTheDocument();
  });

  it('debe renderizar datos de incapacidad ARL con empleado y empresa', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Información General
    expect(screen.getByText('INC-2024-001')).toBeInTheDocument();
    expect(screen.getByText('ARL')).toBeInTheDocument();

    // Paciente (empleado)
    expect(screen.getByText('Juan Carlos Pérez Gómez')).toBeInTheDocument();
    expect(screen.getByText('12345678')).toBeInTheDocument();
    expect(screen.getByText('juan@example.com')).toBeInTheDocument();

    // Empresa
    expect(screen.getByText('Empresa Test SA')).toBeInTheDocument();
    expect(screen.getByText('900123456')).toBeInTheDocument();

    // Siniestro
    expect(screen.getByText('SIN-2024-001')).toBeInTheDocument();
    expect(screen.getByText('Caída en escaleras')).toBeInTheDocument();
  });

  it('debe renderizar datos de incapacidad SALUD con afiliado', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadSalud} />);

    // Información General
    expect(screen.getByText('INC-2024-002')).toBeInTheDocument();
    expect(screen.getByText('SALUD')).toBeInTheDocument();

    // Paciente (afiliado)
    expect(screen.getByText('María López')).toBeInTheDocument();
    expect(screen.getByText('87654321')).toBeInTheDocument();
    expect(screen.getByText('maria@example.com')).toBeInTheDocument();
    expect(screen.getByText('POL-2024-001')).toBeInTheDocument();

    // NO debe mostrar datos de empresa ni siniestro
    expect(screen.queryByText('Empresa Test SA')).not.toBeInTheDocument();
    expect(screen.queryByText('Siniestro Asociado')).not.toBeInTheDocument();
  });

  it('debe mostrar badges con colores correctos según estado y prioridad', () => {
    const { rerender } = render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Estado: EN_AUDITORIA (amarillo/warning)
    const estadoBadge = screen.getByText('EN_AUDITORIA');
    expect(estadoBadge).toHaveClass('bg-yellow-100');

    // Prioridad: ALTA (rojo/destructive)
    const prioridadBadge = screen.getByText('ALTA');
    expect(prioridadBadge).toHaveClass('bg-red-100');

    // Cambiar a incapacidad APROBADA
    const incapacidadAprobada = {
      ...mockIncapacidadSalud,
      estado: EstadoIncapacidad.APROBADA,
      prioridad: 'NORMAL',
    };
    rerender(<IncapacidadDetalle incapacidad={incapacidadAprobada} />);

    // Estado: APROBADA (verde/success)
    const estadoBadgeAprobada = screen.getByText('APROBADA');
    expect(estadoBadgeAprobada).toHaveClass('bg-green-100');

    // Prioridad: NORMAL (gris/secondary)
    const prioridadBadgeNormal = screen.getByText('NORMAL');
    expect(prioridadBadgeNormal).toHaveClass('bg-slate-100');
  });

  it('debe formatear valores monetarios correctamente', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Debe mostrar valores monetarios con formato colombiano
    expect(screen.getByText('$500,000')).toBeInTheDocument();
    expect(screen.getByText('$100,000')).toBeInTheDocument();
  });

  it('debe mostrar "No especificado" cuando faltan datos opcionales', () => {
    const incapacidadSinObservaciones = {
      ...mockIncapacidadSalud,
      observaciones: null,
    };

    render(<IncapacidadDetalle incapacidad={incapacidadSinObservaciones} />);

    // Debe mostrar placeholder para observaciones vacías
    expect(screen.getByText('No hay observaciones')).toBeInTheDocument();
  });
});
