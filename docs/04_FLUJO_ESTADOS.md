# Flujo de Estados - Sistema de Gestión de Incapacidades

## 1. Diagrama de Estados

```
                    ┌─────────────┐
                    │   INICIO    │
                    └──────┬──────┘
                           │
                           │ Radicación
                           ▼
                    ┌─────────────┐
              ┌─────┤  RADICADA   ├─────┐
              │     └──────┬──────┘     │
              │            │            │
              │            │ Asignar    │
              │            │ a auditoría│
              │            ▼            │
              │     ┌─────────────┐    │
              │     │EN_AUDITORIA │◄───┤
              │     └──────┬──────┘    │
              │            │            │
              │     ┌──────┴───────┬───┴─────────┐
              │     │              │             │
              │     │ Solicitar    │ Aprobar     │ Rechazar
              │     │ información  │             │
              │     ▼              ▼             ▼
              │  ┌──────────┐  ┌─────────┐  ┌──────────┐
              │  │OBSERVADA │  │APROBADA │  │RECHAZADA │
              │  └────┬─────┘  └────┬────┘  └──────────┘
              │       │             │              │
              │       │ Responder   │ Generar      │
              │       │ observac.   │ orden pago   │
              │       │             ▼              │
              │       └────────►┌─────────┐       │
              │                 │ EN_PAGO │       │
              │                 └────┬────┘       │
              │                      │            │
              │                      │ Confirmar  │
              │                      │ pago       │
              │                      ▼            │
              │                 ┌─────────┐      │
              │                 │ PAGADA  │      │
              │                 └─────────┘      │
              │                                  │
              │ Cancelar                         │
              └─────────────────────────────────►│
                                                 ▼
                                          ┌──────────┐
                                          │CANCELADA │
                                          └──────────┘
```

## 2. Descripción de Estados

### 2.1 RADICADA

**Descripción**: Estado inicial cuando se registra una nueva incapacidad en el sistema.

**Acciones permitidas**:
- Adjuntar documentos
- Editar información (si no ha iniciado auditoría)
- Cancelar radicación
- Asignar a auditoría

**Usuarios con permiso**:
- Empresa (creador)
- Empleado (creador)
- Admin
- Auditor (solo lectura)

**Notificaciones**:
- Email a la empresa confirmando radicación
- Email al empleado confirmando radicación

### 2.2 EN_AUDITORIA

**Descripción**: La incapacidad está siendo revisada por un auditor.

**Acciones permitidas**:
- Revisar documentos
- Solicitar información adicional (→ OBSERVADA)
- Aprobar (→ APROBADA)
- Rechazar (→ RECHAZADA)
- Reasignar a otro auditor

**Usuarios con permiso**:
- Auditor asignado
- Admin

**Validaciones**:
- Todos los documentos obligatorios están adjuntos
- Fechas de incapacidad son válidas
- Empleado está activo
- Empresa está activa

**Notificaciones**:
- Email al auditor asignado

### 2.3 OBSERVADA

**Descripción**: El auditor ha solicitado información adicional o correcciones.

**Acciones permitidas**:
- Responder observaciones (→ EN_AUDITORIA)
- Adjuntar documentos faltantes
- Actualizar información
- Cancelar radicación (→ CANCELADA)

**Usuarios con permiso**:
- Empresa (creador)
- Empleado (creador)
- Admin

**Notificaciones**:
- Email a la empresa con detalles de observaciones
- Email al empleado con observaciones
- Recordatorio automático después de 5 días

**SLA**: 10 días hábiles para responder

### 2.4 APROBADA

**Descripción**: La incapacidad ha sido aprobada tras auditoría exitosa.

**Acciones permitidas**:
- Generar orden de pago (→ EN_PAGO)
- Anular aprobación (solo Admin)

**Usuarios con permiso**:
- Admin
- Auditor (solo generar orden de pago)

**Validaciones automáticas**:
- Cálculo de valor a pagar
- Verificación de cuenta bancaria del beneficiario
- Generación de número de orden

**Notificaciones**:
- Email a la empresa confirmando aprobación
- Email al empleado confirmando aprobación

### 2.5 EN_PAGO

**Descripción**: Se ha generado orden de pago y está en proceso.

**Acciones permitidas**:
- Registrar pago efectuado (→ PAGADA)
- Anular orden de pago (→ APROBADA)
- Consultar estado de pago

**Usuarios con permiso**:
- Admin
- Usuario con rol TESORERIA

**Validaciones**:
- Orden de pago generada
- Datos bancarios completos

**Notificaciones**:
- Email al área de tesorería

### 2.6 PAGADA

**Descripción**: El pago ha sido efectuado exitosamente.

**Acciones permitidas**:
- Consultar detalles
- Descargar comprobante de pago
- Generar certificados

**Usuarios con permiso**:
- Todos (solo lectura)

**Validaciones**:
- Comprobante de pago adjuntado
- Fecha de pago registrada
- Referencia de transacción

**Notificaciones**:
- Email a la empresa confirmando pago
- Email al empleado confirmando pago
- Certificado de pago generado

**Archivado**: Después de 90 días, se archiva en storage de largo plazo

### 2.7 RECHAZADA

**Descripción**: La incapacidad ha sido rechazada tras auditoría.

**Acciones permitidas**:
- Consultar motivo de rechazo
- Crear nueva radicación (opcional)

**Usuarios con permiso**:
- Todos (solo lectura)

**Validaciones**:
- Motivo de rechazo obligatorio
- Auditor asignado registrado

**Notificaciones**:
- Email a la empresa con motivo de rechazo
- Email al empleado con motivo de rechazo

### 2.8 CANCELADA

**Descripción**: La radicación ha sido cancelada por el solicitante o Admin.

**Acciones permitidas**:
- Consultar detalles

**Usuarios con permiso**:
- Todos (solo lectura)

**Validaciones**:
- Motivo de cancelación obligatorio
- Solo puede cancelarse en estados: RADICADA, OBSERVADA

**Notificaciones**:
- Email confirmando cancelación

## 3. Matriz de Transiciones

| Estado Actual  | Estado Destino  | Acción                | Rol Permitido        | Validaciones                    |
|----------------|-----------------|----------------------|----------------------|---------------------------------|
| RADICADA       | EN_AUDITORIA    | Asignar auditoría    | Admin, Auditor       | Documentos mínimos adjuntos     |
| RADICADA       | CANCELADA       | Cancelar             | Creador, Admin       | Motivo obligatorio              |
| EN_AUDITORIA   | OBSERVADA       | Solicitar info       | Auditor, Admin       | Observaciones obligatorias      |
| EN_AUDITORIA   | APROBADA        | Aprobar              | Auditor, Admin       | Validación completa             |
| EN_AUDITORIA   | RECHAZADA       | Rechazar             | Auditor, Admin       | Motivo obligatorio              |
| OBSERVADA      | EN_AUDITORIA    | Responder            | Creador, Admin       | Respuesta a observaciones       |
| OBSERVADA      | CANCELADA       | Cancelar             | Creador, Admin       | Motivo obligatorio              |
| APROBADA       | EN_PAGO         | Generar orden        | Admin, Auditor       | Datos bancarios completos       |
| APROBADA       | RADICADA        | Anular aprobación    | Admin                | Motivo obligatorio              |
| EN_PAGO        | PAGADA          | Registrar pago       | Admin, Tesorería     | Comprobante y referencia        |
| EN_PAGO        | APROBADA        | Anular orden         | Admin                | Motivo obligatorio              |

## 4. Reglas de Negocio por Estado

### 4.1 Al Radicar (Estado: RADICADA)

```python
validaciones = {
    "empleado_activo": True,
    "empresa_activa": True,
    "fechas_validas": fecha_fin >= fecha_inicio,
    "dias_calculados": (fecha_fin - fecha_inicio).days + 1,
    "no_solapamiento": no existe otra incapacidad en mismo rango,
    "tipo_valido": tipo in ["ARL", "SALUD"],
    "documentos_minimos": al menos 1 documento adjunto
}
```

**Auto-cálculos**:
- Número consecutivo único
- Días totales
- Valor por día (según salario base)
- Valor total

### 4.2 Al Auditar (Estado: EN_AUDITORIA)

```python
validaciones = {
    "documentos_obligatorios": [
        "INCAPACIDAD_MEDICA",
        "CEDULA"
    ],
    "diagnostico_cie10_valido": True,
    "fechas_coherentes": True,
    "valor_calculado_correcto": True,
    "empleado_con_cuenta_bancaria": True
}
```

**SLA**: 5 días hábiles para completar auditoría

### 4.3 Al Observar (Estado: OBSERVADA)

```python
validaciones = {
    "observaciones_no_vacias": len(observaciones) > 10,
    "documentos_faltantes_especificados": True
}
```

**Auto-acciones**:
- Notificación inmediata a creador
- Recordatorio automático cada 5 días
- Escalamiento a Admin después de 15 días

### 4.4 Al Aprobar (Estado: APROBADA)

```python
validaciones = {
    "todas_validaciones_auditoria_ok": True,
    "valor_dentro_limites": valor_total <= parametro("VALOR_MAX_INCAPACIDAD"),
    "empleado_cuenta_bancaria": cuenta_bancaria is not None
}
```

**Auto-acciones**:
- Calcular valor final a pagar
- Preparar datos para orden de pago
- Actualizar estadísticas

### 4.5 Al Generar Orden de Pago (Estado: EN_PAGO)

```python
validaciones = {
    "estado_aprobada": True,
    "orden_pago_no_existe": not tiene_orden_pago_activa,
    "beneficiario_datos_completos": {
        "nombre": True,
        "documento": True,
        "cuenta_bancaria": True,
        "banco": True
    }
}
```

**Auto-acciones**:
- Generar número de orden consecutivo
- Crear registro en tabla orden_pago
- Bloquear ediciones de incapacidad

### 4.6 Al Registrar Pago (Estado: PAGADA)

```python
validaciones = {
    "orden_pago_aprobada": True,
    "fecha_pago_valida": fecha_pago <= fecha_actual,
    "referencia_pago_unica": True,
    "comprobante_adjunto": True
}
```

**Auto-acciones**:
- Actualizar estado de orden de pago
- Generar certificado de pago
- Archivar documentos
- Cerrar caso

### 4.7 Al Rechazar (Estado: RECHAZADA)

```python
validaciones = {
    "motivo_rechazo_obligatorio": len(motivo_rechazo) >= 20,
    "motivo_en_catalogo": motivo in MOTIVOS_RECHAZO_VALIDOS
}
```

**Catálogo de motivos de rechazo**:
- Documentación incompleta
- Fechas incoherentes
- Diagnóstico no válido
- Duplicado
- Fuera de cobertura
- Empleado inactivo
- Otros (especificar)

## 5. Tiempos y SLAs

| Estado          | SLA                    | Acción Escalamiento                  |
|-----------------|------------------------|--------------------------------------|
| RADICADA        | 1 día hábil            | Asignar automáticamente a auditor    |
| EN_AUDITORIA    | 5 días hábiles         | Notificar a supervisor               |
| OBSERVADA       | 10 días hábiles        | Escalar a Admin                      |
| APROBADA        | 3 días hábiles         | Generar orden de pago automática     |
| EN_PAGO         | 10 días hábiles        | Notificar a gerencia financiera      |

## 6. Eventos y Webhooks

### 6.1 Eventos Emitidos

```python
eventos = {
    "incapacidad.radicada": {
        "payload": {
            "incapacidad_id": "uuid",
            "numero": "INC-202601-000001",
            "empleado": {...},
            "empresa": {...}
        }
    },
    "incapacidad.estado_cambiado": {
        "payload": {
            "incapacidad_id": "uuid",
            "estado_anterior": "RADICADA",
            "estado_nuevo": "EN_AUDITORIA",
            "cambiado_por": "usuario_id"
        }
    },
    "incapacidad.observada": {
        "payload": {
            "incapacidad_id": "uuid",
            "observaciones": "texto",
            "auditor": {...}
        }
    },
    "incapacidad.aprobada": {
        "payload": {
            "incapacidad_id": "uuid",
            "valor_total": 500000,
            "aprobado_por": {...}
        }
    },
    "incapacidad.rechazada": {
        "payload": {
            "incapacidad_id": "uuid",
            "motivo_rechazo": "texto"
        }
    },
    "orden_pago.generada": {
        "payload": {
            "orden_pago_id": "uuid",
            "numero_orden": "OP-202601-000001",
            "valor": 500000
        }
    },
    "orden_pago.pagada": {
        "payload": {
            "orden_pago_id": "uuid",
            "fecha_pago": "2026-01-06",
            "referencia": "TRX123"
        }
    }
}
```

### 6.2 Suscriptores de Eventos

- Sistema de notificaciones (Email, SMS)
- Sistema de auditoría
- Dashboard de métricas
- Sistemas externos (ERP, Contabilidad)

## 7. Validaciones de Integridad

### 7.1 Validaciones Generales

```sql
-- No permitir cambios de estado inválidos
CREATE OR REPLACE FUNCTION validar_transicion_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM transiciones_estado_validas
        WHERE estado_origen = OLD.estado
        AND estado_destino = NEW.estado
    ) THEN
        RAISE EXCEPTION 'Transición de estado no válida: % -> %', 
            OLD.estado, NEW.estado;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 7.2 Validaciones por Estado

```python
class EstadoValidator:
    @staticmethod
    def validar_radicada(incapacidad):
        assert incapacidad.empleado.estado == "ACTIVO"
        assert incapacidad.empresa.estado == "ACTIVA"
        assert incapacidad.fecha_fin >= incapacidad.fecha_inicio
        assert len(incapacidad.documentos) >= 1
    
    @staticmethod
    def validar_en_auditoria(incapacidad):
        assert incapacidad.auditado_por_id is not None
        assert all([
            doc.tipo_documento in DOCUMENTOS_OBLIGATORIOS
            for doc in incapacidad.documentos
        ])
    
    @staticmethod
    def validar_aprobada(incapacidad):
        assert incapacidad.valor_total > 0
        assert incapacidad.empleado.cuenta_bancaria is not None
        assert incapacidad.aprobado_por_id is not None
    
    @staticmethod
    def validar_en_pago(incapacidad):
        assert incapacidad.orden_pago is not None
        assert incapacidad.orden_pago.estado_pago in ["GENERADA", "APROBADA"]
    
    @staticmethod
    def validar_pagada(incapacidad):
        assert incapacidad.orden_pago.fecha_pago is not None
        assert incapacidad.orden_pago.referencia_pago is not None
```

## 8. Reportes por Estado

### 8.1 Dashboard de Estados

```sql
-- Resumen de incapacidades por estado
SELECT 
    estado,
    COUNT(*) as total,
    SUM(valor_total) as valor_total,
    AVG(EXTRACT(EPOCH FROM (COALESCE(updated_at, NOW()) - created_at))/86400) 
        as dias_promedio_en_estado
FROM incapacidad
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY estado
ORDER BY 
    CASE estado
        WHEN 'RADICADA' THEN 1
        WHEN 'EN_AUDITORIA' THEN 2
        WHEN 'OBSERVADA' THEN 3
        WHEN 'APROBADA' THEN 4
        WHEN 'EN_PAGO' THEN 5
        WHEN 'PAGADA' THEN 6
        WHEN 'RECHAZADA' THEN 7
        WHEN 'CANCELADA' THEN 8
    END;
```

### 8.2 Alertas por Vencimiento de SLA

```sql
-- Incapacidades que exceden SLA
SELECT 
    i.id,
    i.numero,
    i.estado,
    e.nombres || ' ' || e.apellidos as empleado,
    emp.razon_social as empresa,
    EXTRACT(EPOCH FROM (NOW() - i.created_at))/86400 as dias_en_estado,
    CASE i.estado
        WHEN 'RADICADA' THEN 1
        WHEN 'EN_AUDITORIA' THEN 5
        WHEN 'OBSERVADA' THEN 10
        WHEN 'APROBADA' THEN 3
        WHEN 'EN_PAGO' THEN 10
    END as sla_dias
FROM incapacidad i
JOIN empleado e ON i.empleado_id = e.id
JOIN empresa emp ON i.empresa_id = emp.id
WHERE i.estado IN ('RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 'EN_PAGO')
AND EXTRACT(EPOCH FROM (NOW() - i.created_at))/86400 > 
    CASE i.estado
        WHEN 'RADICADA' THEN 1
        WHEN 'EN_AUDITORIA' THEN 5
        WHEN 'OBSERVADA' THEN 10
        WHEN 'APROBADA' THEN 3
        WHEN 'EN_PAGO' THEN 10
    END
ORDER BY dias_en_estado DESC;
```
