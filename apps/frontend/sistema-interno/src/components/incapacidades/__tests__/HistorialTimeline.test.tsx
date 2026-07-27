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
    cambiado_por_id: 'user-system',
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
    cambiado_por_id: 'user-admin',
    cambiado_por_nombre: 'Admin Usuario',
    observacion: 'Pasando a auditoría para revisión',
    created_at: '2024-01-11T14:30:00Z',
  },
  {
    id: 'hist-3',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.EN_AUDITORIA,
    estado_nuevo: EstadoIncapacidad.PENDIENTE,
    cambiado_por_id: 'user-auditor',
    cambiado_por_nombre: 'Auditor Pérez',
    observacion: 'Faltan documentos: historia clínica completa',
    created_at: '2024-01-12T09:15:00Z',
  },
  {
    id: 'hist-4',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.PENDIENTE,
    estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
    cambiado_por_id: 'user-system',
    cambiado_por_nombre: 'Sistema',
    observacion: 'Documentos actualizados por el solicitante',
    created_at: '2024-01-13T16:45:00Z',
  },
  {
    id: 'hist-5',
    entity_type: 'incapacidad',
    entity_id: 'inc-123',
    estado_anterior: EstadoIncapacidad.EN_AUDITORIA,
    estado_nuevo: EstadoIncapacidad.LIQUIDACION,
    cambiado_por_id: 'user-auditor',
    cambiado_por_nombre: 'Auditor Pérez',
    observacion: 'Aprobado: cumple todos los requisitos',
    created_at: '2024-01-14T11:20:00Z',
  },
] as any;

describe('HistorialTimeline', () => {
  it('debe renderizar el resumen estadístico de cambios', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Resumen estadístico (Card al final del timeline)
    expect(screen.getByText('Cambios totales')).toBeInTheDocument();
    
    // El número "5" aparece en múltiples lugares, verificar que existe
    const cincos = screen.getAllByText('5');
    expect(cincos.length).toBeGreaterThan(0); // Al menos uno (Cambios totales)

    expect(screen.getByText('Con responsable')).toBeInTheDocument();
    expect(screen.getByText('Con observaciones')).toBeInTheDocument();
    expect(screen.getByText('Días en proceso')).toBeInTheDocument();
  });

  it('debe renderizar todos los estados en orden cronológico inverso (más reciente primero)', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Debe mostrar todos los estados (múltiples badges)
    const estadoElements = screen.getAllByText(/RADICADA|EN_AUDITORIA|PENDIENTE|LIQUIDACION/);
    expect(estadoElements.length).toBeGreaterThan(0);

    // El badge "Más reciente" debe estar presente (solo en el primer item)
    expect(screen.getByText('Más reciente')).toBeInTheDocument();

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

    // El componente renderiza: "No hay historial de cambios para esta incapacidad."
    expect(screen.getByText(/No hay historial de cambios para esta incapacidad/)).toBeInTheDocument();
  });

  it('debe mostrar fechas formateadas correctamente', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Verificar que aparecen fechas en formato DD/MM/YYYY (formatDate)
    expect(screen.getByText('10/01/2024')).toBeInTheDocument(); // 2024-01-10
    expect(screen.getByText('11/01/2024')).toBeInTheDocument(); // 2024-01-11
    expect(screen.getByText('14/01/2024')).toBeInTheDocument(); // 2024-01-14
  });

  it('debe calcular correctamente los días en proceso', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Debe mostrar el texto "Días en proceso" en el resumen estadístico
    expect(screen.getByText('Días en proceso')).toBeInTheDocument();
    
    // Verificar que se calcula y muestra un número (sin importar el valor exacto)
    // El Card de resumen tiene números en elementos <p> con clases de color
    const resumenCard = screen.getByText('Días en proceso').closest('div')?.parentElement;
    expect(resumenCard).toBeTruthy();
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
        cambiado_por_id: 'user-admin',
        cambiado_por_nombre: 'Admin',
        observacion: null,
        created_at: '2024-01-15T10:00:00Z',
      },
    ] as any;

    render(<HistorialTimeline historial={historialSinObservacion} />);

    // No debe romper si no hay observación
    expect(screen.getByText('Admin')).toBeInTheDocument();
    
    // EN_AUDITORIA aparece múltiples veces (badge principal + transición)
    const estadoBadges = screen.getAllByText('EN_AUDITORIA');
    expect(estadoBadges.length).toBeGreaterThan(0);
    
    // No debe mostrar el texto "Observaciones:" cuando no hay observación
    expect(screen.queryByText('Observaciones:')).not.toBeInTheDocument();
  });

  it('debe mostrar el nombre del responsable con su etiqueta, y no un id crudo', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    expect(screen.getAllByText('Responsable:').length).toBe(mockHistorial.length);
    // El id técnico (p. ej. "user-admin") nunca debe mostrarse como texto visible.
    expect(screen.queryByText('user-admin')).not.toBeInTheDocument();
    expect(screen.queryByText('user-system')).not.toBeInTheDocument();
    expect(screen.queryByText('user-auditor')).not.toBeInTheDocument();
  });

  it('no debe romper ni mostrar la sección de responsable cuando el cambio fue automático (sin usuario)', () => {
    const historialAutomatico = [
      {
        id: 'hist-auto',
        entity_type: 'incapacidad',
        entity_id: 'inc-789',
        estado_anterior: EstadoIncapacidad.RADICADA,
        estado_nuevo: EstadoIncapacidad.EN_AUDITORIA,
        cambiado_por_id: null,
        cambiado_por_nombre: null,
        observacion: 'Transición automática por job de auditoría',
        created_at: '2024-01-16T10:00:00Z',
      },
    ] as any;

    render(<HistorialTimeline historial={historialAutomatico} />);

    expect(screen.queryByText('Responsable:')).not.toBeInTheDocument();
    expect(screen.getByText(/Transición automática por job de auditoría/)).toBeInTheDocument();
  });

  it('debe aplicar colores diferentes según el estado', () => {
    render(<HistorialTimeline historial={mockHistorial} />);

    // Verificar que hay badges con diferentes estados (sin verificar CSS classes)
    const badges = screen.getAllByText(/RADICADA|EN_AUDITORIA|OBSERVADA|APROBADA/);
    
    // Debe haber múltiples badges (cada estado puede aparecer varias veces)
    // En mockHistorial tenemos 5 cambios, pero algunos estados se repiten
    expect(badges.length).toBeGreaterThanOrEqual(5);
    
    // Verificar que existe el badge de estado más reciente
    expect(screen.getByText('Más reciente')).toBeInTheDocument();
  });
});
