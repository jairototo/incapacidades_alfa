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
              │     ┌──────┴───────┬───┴─────────┬─────────────┐
              │     │              │             │             │
              │     │ Solicitar    │ Aprobar     │ Aprobar     │ Rechazar
              │     │ información  │ 100%        │ Parcial     │
              │     ▼              ▼             ▼             ▼
              │  ┌──────────┐  ┌─────────┐  ┌──────────────┐  ┌──────────┐
              │  │PENDIENTE │  │APR LIQU │  │APROBADA_PARC.│  │GLOSADA   │
              │  └────┬─────┘  └────┬────┘  └──────┬───────┘  └──────────┘
              │       │             │               │                │
              │       │ Responder   │ Generar       │ Generar        │
              │       │ observac.   │ orden pago    │ orden pago     │
              │       │             │ completa      │ parcial        │
              │       │             ▼               ▼                │
              │       └────────►┌─────────┐     ┌────────────────┐  │
              │                 │ EN_PAGO │     │EN_PAGO_PARCIAL │  │
              │                 └────┬────┘     └───────┬────────┘  │
              │                      │                  │            │
              │                      │ Confirmar        │ Confirmar  │
              │                      │ pago 100%        │ pago parc. │
              │                      ▼                  ▼            │
              │                 ┌─────────┐      ┌──────────────┐   │
              │                 │ PAGADA  │      │PAGADA_PARC.  │   │
              │                 └─────────┘      └──────────────┘   │
              │                                                      │
              │ Cancelar                                             │
              └─────────────────────────────────────────────────────►│
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

**NOTA PARA ARPIS**:

Recibo por XXXX (Onbase o Imaginex) Incapacidad de la IPS XXXXXX Con fecha de expedición del XX/XX/XXXX por XX días, con fecha de inicio del XX/XX/XXXX al XX/XX/XXXX por el Diagnostico: XXXXXX , firmada por (especialista/ Nombre del médico) XXXXXXX. se autoriza pago de incapacidad por xx días

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

---

### 2.9 APROBADA_PARCIALMENTE

**Descripción**: La incapacidad ha sido aprobada **parcialmente** porque el auditor determinó que los días a aprobar son menores a los solicitados.

**Acciones permitidas**:
- Generar orden de pago parcial (→ EN_PAGO_PARCIAL)
- Anular aprobación parcial (solo Admin)
- Consultar detalles y datos aprobados

**Usuarios con permiso**:
- Admin
- Auditor (solo generar orden de pago)

**Diferencia con APROBADA**:
- Los datos aprobados (fechas, días, CIE-10, diagnóstico) se guardan en tabla `auditoria_datos_aprobados`
- El valor a pagar se calcula con base en `dias_aprobados` (no `dias_totales`)
- Se mantienen tanto los datos originales como los aprobados para trazabilidad

**Datos almacenados**:
- `fecha_inicio_aprobada`: Fecha de inicio aprobada por el auditor
- `fecha_fin_aprobada`: Fecha de fin aprobada por el auditor
- `dias_aprobados`: Cantidad de días aprobados (menor a `dias_totales`)
- `cie10_aprobado`: Código CIE-10 aprobado (puede diferir del solicitado)
- `diagnostico_aprobado`: Descripción del diagnóstico aprobado
- `observacion_auditoria`: Justificación del auditor para la aprobación parcial

**Validaciones**:
- `dias_aprobados` debe ser >= 1 y < `dias_totales` de la incapacidad
- Todos los campos de datos aprobados son obligatorios
- `observacion_auditoria` debe explicar las modificaciones

**Notificaciones**:
- Email a la empresa indicando aprobación parcial
- Email al empleado/afiliado indicando días aprobados vs solicitados
- Detalle de las diferencias en el cuerpo del email

---

### 2.10 EN_PAGO_PARCIAL

**Descripción**: Se ha generado orden de pago **parcial** y está en proceso de pago.

**Acciones permitidas**:
- Registrar pago efectuado (→ PAGADA_PARCIALMENTE)
- Anular orden de pago (→ APROBADA_PARCIALMENTE)
- Consultar detalles de la orden

**Usuarios con permiso**:
- Admin
- Usuario con rol TESORERIA (si existe)

**Cálculo de valor de pago**:
- Se usa `dias_aprobados` en lugar de `dias_totales`
- Fórmula: `valor_pago_parcial = valor_dia * dias_aprobados`
- Ejemplo: Si se solicitaron 10 días pero se aprobaron 5, se paga solo por 5 días

**Validaciones**:
- Debe existir registro en `auditoria_datos_aprobados`
- Datos bancarios del empleado/afiliado completos
- Orden de pago generada y en estado APROBADA

**Notificaciones**:
- Email a Tesorería con orden de pago parcial
- Email a la empresa con detalle de pago parcial pendiente

---

### 2.11 PAGADA_PARCIALMENTE

**Descripción**: El pago **parcial** ha sido efectuado exitosamente.

**Acciones permitidas**:
- Consultar detalles
- Descargar comprobante de pago parcial
- Generar certificados de pago
- Ver comparativa solicitado vs aprobado vs pagado

**Información visible**:
- Días solicitados vs días aprobados vs días pagados
- Valor solicitado vs valor aprobado vs valor pagado
- Motivo de la aprobación parcial (observación del auditor)
- Datos bancarios utilizados para el pago
- Comprobante de pago

**Usuarios con permiso**:
- Todos (solo consulta)
- Admin (gestión completa)

**Diferencias con PAGADA completa**:
- Muestra indicador visual de "PAGO PARCIAL"
- Incluye sección de comparativa en el detalle
- Emails y certificados incluyen mención de pago parcial

**Validaciones**:
- Orden de pago en estado PAGADA
- Comprobante de pago adjunto
- Referencia bancaria registrada

**Notificaciones**:
- Email a la empresa confirmando pago parcial
- Email al empleado/afiliado confirmando pago parcial con:
  - Valor pagado
  - Días aprobados
  - Justificación de la diferencia
  - Comprobante de pago adjunto

**Reportes y auditoría**:
- Los pagos parciales se marcan claramente en reportes
- Incluidos en dashboard de métricas con indicador especial
- Estadísticas separadas: % de aprobaciones parciales, promedio de días reducidos, etc.

---

## 3. Matriz de Transiciones

| Estado Actual           | Estado Destino         | Acción                  | Rol Permitido    | Validaciones                    |
|-------------------------|------------------------|-------------------------|------------------|---------------------------------|
| RADICADA                | EN_AUDITORIA           | Asignar auditoría       | Admin, Auditor   | Documentos mínimos adjuntos     |
| RADICADA                | CANCELADA              | Cancelar                | Creador, Admin   | Motivo obligatorio              |
| EN_AUDITORIA            | OBSERVADA              | Solicitar info          | Auditor, Admin   | Observaciones obligatorias      |
| EN_AUDITORIA            | APROBADA               | Aprobar 100%            | Auditor, Admin   | Validación completa             |
| EN_AUDITORIA            | APROBADA_PARCIALMENTE  | Aprobar parcial         | Auditor, Admin   | Datos aprobados obligatorios    |
| EN_AUDITORIA            | RECHAZADA              | Rechazar                | Auditor, Admin   | Motivo obligatorio              |
| OBSERVADA               | EN_AUDITORIA           | Responder               | Creador, Admin   | Respuesta a observaciones       |
| OBSERVADA               | CANCELADA              | Cancelar                | Creador, Admin   | Motivo obligatorio              |
| APROBADA                | EN_PAGO                | Generar orden completa  | Admin, Auditor   | Datos bancarios completos       |
| APROBADA                | RADICADA               | Anular aprobación       | Admin            | Motivo obligatorio              |
| APROBADA_PARCIALMENTE   | EN_PAGO_PARCIAL        | Generar orden parcial   | Admin, Auditor   | Datos bancarios completos       |
| APROBADA_PARCIALMENTE   | CANCELADA              | Cancelar                | Admin            | Motivo obligatorio              |
| EN_PAGO                 | PAGADA                 | Registrar pago 100%     | Admin, Tesorería | Comprobante y referencia        |
| EN_PAGO                 | APROBADA               | Anular orden            | Admin            | Motivo obligatorio              |
| EN_PAGO_PARCIAL         | PAGADA_PARCIALMENTE    | Registrar pago parcial  | Admin, Tesorería | Comprobante y referencia        |
| EN_PAGO_PARCIAL         | APROBADA_PARCIALMENTE  | Anular orden parcial    | Admin            | Motivo obligatorio              |

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

---

## 9. Flujo Unificado Pre-Incapacidad → Incapacidad (desde 2026-06-09)

> **Nota (2026-06-20):** este flujo (pre-incapacidad → job → incapacidad) es el
> **flujo legado**, aún presente en el backend. El **Portal Externo** (empresa
> autenticada, radicación individual y masiva) **no lo usa**: crea la
> `Incapacidad` directamente mediante el `RadicacionPipelineService` compartido y
> transiciona `RADICADA → EN_AUDITORIA` sin pasar por `PreIncapacidad`. Ver
> [`../superpowers/PR-portal-externo-empresa-refactor.md`](../superpowers/PR-portal-externo-empresa-refactor.md).

El job de Celery `promote_pre_incapacidad_task` crea directamente una `Incapacidad` completa
desde la `PreIncapacidad` en un solo paso:

1. **Portal externo** radica `PreIncapacidad` → estado `PENDIENTE`
2. **Celery job** (`promote_pre_incapacidad_task`) se ejecuta:
   a. Resuelve empresa (por NIT) y empleado (por documento + empresa_id) — pueden no encontrarse
   b. Corre `PreIncapacidadValidationService.validate_all()` — guarda issues en `validation_inconsistencia`
   c. Crea `Incapacidad` directamente con `numero = str(pre_incapacidad.numero_radicacion)`
   d. Vincula `pre_incapacidad.incapacidad_id = incapacidad.id`
   e. Si empleado encontrado: corre reglas RN008/RN009 de auditoría (traslapes + duplicados)
   f. Llama `radicar_incapacidad()` → `Incapacidad` pasa de `RADICADA` a `EN_AUDITORIA`
   g. Actualiza `PreIncapacidad.estado = PROCESADA`
3. **Gestión interna** (`/pre-incapacidades/{id}/gestionar`):
   - Muestra `validation_inconsistencias` con alertas de empleado/empresa no encontrado como WARNING
   - Muestra "Incapacidad N°XXX creada" con estado actual de la incapacidad
   - Permite "Promover manualmente" para re-ejecutar el job si se corrigieron datos

### Manejo de empleado/empresa no encontrado

Cuando el empleado o la empresa no se encuentran en la BD:
- Se crea la incapacidad con `empleado_id = NULL` y/o `empresa_id = NULL`
- Se registra un WARNING `EMPLEADO_NOT_FOUND` / `EMPRESA_NOT_FOUND` en `validation_inconsistencia`
- La incapacidad pasa a `EN_AUDITORIA` — el auditor puede resolver manualmente

### Constraint DB relajado (migración `unified_flow_relax_arl_constraint_add_incapacidad_fk`)

```sql
-- Nuevo constraint — ARL no requiere empleado_id / empresa_id NOT NULL
(tipo = 'ARL' AND afiliado_id IS NULL) OR
(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
```
