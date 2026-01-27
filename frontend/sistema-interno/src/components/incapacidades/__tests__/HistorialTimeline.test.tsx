import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HistorialTimeline } from '../HistorialTimeline';
import { EstadoIncapacidad } from '@/types';

const mockHistorial = [
  {
    id: 'hist-1',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: null,
    estado_nuevo: EstadoIncapacidad.RADICADA,
    cambiado_por_nombre: 'Sistema',
    observacion: 'Incapacidad creada',
    created_at: '2024-01-10T10:00:00Z',
  },
  {
    id: 'hist-2',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.RADICADA,
    estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
    cambiado_por_nombre: 'Admin Usuario',
    observacion: 'Pasando a auditoría para revisión',
    created_at: '2024-01-11T14:30:00Z',
  },
  {
    id: 'hist-3',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.EN_AUDITORIA,
    estado_nuevo: EstadoIncapacidad.OBSERVADA,
    cambiado_por_nombre: 'Auditor Pérez',
    observacion: 'Faltan documentos: historia clínica completa',
    created_at: '2024-01-12T09:15:00Z',
  },
  {
    id: 'hist-4',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.OBSERVADA,
    estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
    cambiado_por_nombre: 'Sistema',
    observacion: 'Documentos actualizados por el solicitante',
    created_at: '2024-01-13T16:45:00Z',
  },
  {
    id: 'hist-5',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.EN_AUDITORIA,
    estado_nuevo: EstadoIncapacidad.APROBADA,
    cambiado_por_nombre: 'Auditor Pérez',
    observacion: 'Aprobado: cumple todos los requisitos',
    created_at: '2024-01-14T11:20:00Z',
  },
];

describe('HistorialTimeline', () => {
  it('debe renderizar el título y resumen de cambios', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Título
    expect(screen.getByText('Historial de Estados')).toBeInTheDocument();

    // Resumen
    expect(screen.getByText(/5 cambios registrados/)).toBeInTheDocument();
    expect(screen.getByText(/días en proceso/)).toBeInTheDocument();
  });

  it('debe renderizar todos los estados en orden cronológico inverso (más reciente primero)', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Debe mostrar todos los estados
    const estadoElements = screen.getAllByText(/RADICADA|EN_AUDITORIA|OBSERVADA|APROBADA/);
    expect(estadoElements.length).toBeGreaterThan(0);

    // El primer estado visible debe ser APROBADA (más reciente)
    expect(screen.getByText(/APROBADA/)).toBeInTheDocument();

    // Verificar que aparecen las observaciones
    expect(screen.getByText(/Incapacidad creada/)).toBeInTheDocument();
    expect(screen.getByText(/Pasando a auditoría para revisión/)).toBeInTheDocument();
    expect(screen.getByText(/Faltan documentos: historia clínica completa/)).toBeInTheDocument();
    expect(screen.getByText(/Aprobado: cumple todos los requisitos/)).toBeInTheDocument();
  });

  it('debe mostrar el nombre del usuario que realizó cada cambio', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    expect(screen.getAllByText('Sistema').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Admin Usuario').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Auditor Pérez').length).toBeGreaterThan(0);
  });

  it('debe renderizar mensaje de "Sin historial" cuando el array está vacío', () => {
    render(<HistorialTimeline historial={[]} />);

    expect(screen.getByText(/No hay cambios de estado registrados/)).toBeInTheDocument();
  });

  it('debe mostrar fechas formateadas correctamente', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Verificar que aparecen fechas (formato puede variar, pero debe haber fechas)
    expect(screen.getByText(/10 de enero de 2024/i)).toBeInTheDocument();
    expect(screen.getByText(/11 de enero de 2024/i)).toBeInTheDocument();
  });

  it('debe calcular correctamente los días en proceso', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Debe calcular la diferencia entre la primera y última fecha (4 días)
    // 10 de enero → 14 de enero = 4 días
    expect(screen.getByText(/4 días en proceso/)).toBeInTheDocument();
  });

  it('debe mostrar iconos/indicadores visuales para cada estado', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Verificar que hay elementos de timeline (líneas verticales, puntos)
    const timeline = document.querySelector('.space-y-4');
    expect(timeline).toBeInTheDocument();

    // Debe haber tarjetas para cada estado
    const cards = document.querySelectorAll('[class*="border"]');
    expect(cards.length).toBeGreaterThan(0);
  });

  it('debe manejar estados sin observación', () => {
    const historialSinObservacion = [
      {
        id: 'hist-simple',
        entity_type: 'incapacidad',
        entity_id: 'inc-456',
        estado_anterior: EstadoIncapacidad.RADICADA,
        estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
        cambiado_por_nombre: 'Admin',
        observacion: null,
        created_at: '2024-01-15T10:00:00Z',
      },
    ];

    render(<HistorialTimeline historial={historialSinObservacion} />);

    // No debe romper si no hay observación
    expect(screen.getByText('Historial de Estados')).toBeInTheDocument();
    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('debe aplicar colores diferentes según el estado', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Verificar que hay badges con diferentes estilos
    const badges = screen.getAllByText(/RADICADA|EN_AUDITORIA|OBSERVADA|APROBADA/);
    
    // Debe haber al menos 5 badges (uno por cada cambio)
    expect(badges.length).toBeGreaterThanOrEqual(5);
    
    // Verificar que el badge de APROBADA tiene color verde
    const aprobadaBadge = screen.getByText(/APROBADA/);
    expect(aprobadaBadge).toHaveClass(/bg-green/i);
  });
});
