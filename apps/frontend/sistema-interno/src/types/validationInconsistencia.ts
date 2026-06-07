export type Severidad = 'ERROR' | 'WARNING' | 'INFO';
export type Categoria =
  | 'FIELD_VALIDATION'
  | 'BUSINESS_RULE'
  | 'FRAUD_ALERT'
  | 'INTEGRATION_CHECK';

export interface ValidationInconsistenciaRead {
  id: string;
  pre_incapacidad_id: string;
  incapacidad_id: string | null;
  categoria: Categoria;
  severidad: Severidad;
  codigo: string;
  descripcion: string;
  campo_afectado: string | null;
  valor_encontrado: string | null;
  valor_esperado: string | null;
  fecha_deteccion: string;
}
