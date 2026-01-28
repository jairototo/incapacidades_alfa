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
  it('debe renderizar las cards de información principales', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Verificar que aparecen los títulos de las cards principales
    expect(screen.getByText('Información General')).toBeInTheDocument();
    expect(screen.getByText('Empleado')).toBeInTheDocument(); // Para ARL
    expect(screen.getByText('Empresa')).toBeInTheDocument();
    expect(screen.getByText('Diagnóstico')).toBeInTheDocument();
    expect(screen.getByText('Fechas y Duración')).toBeInTheDocument();
    expect(screen.getByText('Valores')).toBeInTheDocument();
    expect(screen.getByText('Información de Sistema')).toBeInTheDocument();
  });

  it('debe renderizar datos de incapacidad ARL con empleado y empresa', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Información General
    expect(screen.getByText('INC-2024-001')).toBeInTheDocument();
    expect(screen.getByText('ARL')).toBeInTheDocument();

    // Empleado
    expect(screen.getByText('Juan Carlos Pérez Gómez')).toBeInTheDocument();
    expect(screen.getByText('12345678')).toBeInTheDocument();
    expect(screen.getByText('juan@example.com')).toBeInTheDocument();

    // Empresa
    expect(screen.getByText('Empresa Test SA')).toBeInTheDocument();
    expect(screen.getByText('900123456')).toBeInTheDocument();
  });

  it('debe renderizar datos de incapacidad SALUD con afiliado', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadSalud} />);

    // Información General
    expect(screen.getByText('INC-2024-002')).toBeInTheDocument();
    expect(screen.getByText('SALUD')).toBeInTheDocument();

    // Título debe ser 'Afiliado' para tipo SALUD
    expect(screen.getByText('Afiliado')).toBeInTheDocument();

    // Datos del afiliado (solo los que el componente muestra)
    expect(screen.getByText('María López')).toBeInTheDocument();
    expect(screen.getByText('87654321')).toBeInTheDocument();
    // Nota: email y numero_afiliacion NO se muestran en el componente actual

    // NO debe mostrar datos de empresa (solo para ARL)
    expect(screen.queryByText('Empresa Test SA')).not.toBeInTheDocument();
  });

  it('debe mostrar badges con estado y prioridad correctos', () => {
    const { rerender } = render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Debe mostrar estado EN_AUDITORIA
    expect(screen.getByText('EN_AUDITORIA')).toBeInTheDocument();

    // Debe mostrar prioridad ALTA
    expect(screen.getByText('ALTA')).toBeInTheDocument();

    // Cambiar a incapacidad APROBADA con prioridad NORMAL
    const incapacidadAprobada = {
      ...mockIncapacidadSalud,
      estado: EstadoIncapacidad.APROBADA,
      prioridad: 'NORMAL',
    };
    rerender(<IncapacidadDetalle incapacidad={incapacidadAprobada} />);

    // Debe mostrar estado APROBADA
    expect(screen.getByText('APROBADA')).toBeInTheDocument();

    // Debe mostrar prioridad NORMAL
    expect(screen.getByText('NORMAL')).toBeInTheDocument();
  });

  it('debe formatear valores monetarios correctamente', () => {
    render(<IncapacidadDetalle incapacidad={mockIncapacidadARL} />);

    // Debe mostrar valores monetarios con formato colombiano ($ 500.000)
    expect(screen.getByText(/500\.000/)).toBeInTheDocument();
  });

  it('debe ocultar sección de observaciones cuando son null', () => {
    const incapacidadSinObservaciones = {
      ...mockIncapacidadSalud,
      observaciones: null,
    };

    render(<IncapacidadDetalle incapacidad={incapacidadSinObservaciones} />);

    // No debe mostrar el label de observaciones si es null
    expect(screen.queryByText('Observaciones')).not.toBeInTheDocument();
  });
});
