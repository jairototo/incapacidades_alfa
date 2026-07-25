# Scripts de Utilidades

## seed_auditores.py

**⚠️ Prerrequisito obligatorio antes de auditar cualquier incapacidad.**

Script que crea los auditores ficticios (uno por sucursal) y el auditor
`auditor_default` usados por la asignación automática de auditoría
(`app/services/auditor_assignment_service.py`). Si `auditor_default` no
existe en la base de datos, `asignar_auditor()` lanza `RuntimeError`, el
commit de `auditoria_service.auditar_incapacidad` nunca ocurre, y la tarea
de Celery que envuelve la auditoría reintenta 3 veces y finalmente falla —
la incapacidad queda silenciosamente detenida en estado `RADICADA`.

### Uso

```bash
# Dentro del contenedor de la API
docker-compose exec api python scripts/seed_auditores.py

# O usando el target de Makefile (equivalente, ejecutar desde apps/backend/)
make seed-auditores
```

### Datos Creados

El script es idempotente (si un `username` ya existe, lo omite) y crea 8 usuarios
con rol `AUDITOR`, contraseña temporal `Auditor2026!`:

#### Auditores por sucursal (7)
- **auditor.cali** — Camila Restrepo Vargas (sucursal Cali)
- **auditor.medellin** — Santiago Zuluaga Marín (sucursal Medellín)
- **auditor.cartagena** — Valentina Cabrales Ibarra (sucursal Cartagena)
- **auditor.bogota1** — Andrés Felipe Rojas Peña (sucursal Bogotá)
- **auditor.bogota2** — Laura Camila Torres Duque (sucursal Bogotá)
- **auditor.bogota3** — Juan Pablo Medina Salcedo (sucursal Bogotá)
- **auditor.bogota4** — Daniela Ríos Castañeda (sucursal Bogotá)

#### Auditor por defecto (1)
- **auditor_default** — Auditor por Defecto (sin sucursal asignada)

  Usado como fallback cuando una incapacidad SALUD, o una ARL sin siniestro
  activo con sucursal, no puede asignarse a un auditor de sucursal
  específica. Debe permanecer **ACTIVO**: si se desactiva desde
  `AuditoresPage` (módulo admin), toda incapacidad que dependa del fallback
  queda sin auditor asignado y la auditoría automática falla ruidosamente
  (`RuntimeError`) en vez de asignarse silenciosamente a una cuenta
  deshabilitada.

Los nombres/correos son ficticios, deliberadamente distintos a los
auditores reales (ver comentario en el propio script), ya que esos usuarios
reales aún no tienen cuentas en el sistema.

### Prerrequisitos

- Base de datos PostgreSQL con migraciones aplicadas (tabla `usuario` y
  enums `RolUsuario`/`EstadoUsuario`/`SucursalSiniestro` existentes).

## seed_test_data.py

Script para poblar la base de datos con datos de prueba para el sistema de gestión de incapacidades.

### Uso

```bash
# Dentro del contenedor de la API
docker-compose exec api python scripts/seed_test_data.py

# O desde el host
docker-compose exec -T api python scripts/seed_test_data.py
```

### Datos Creados

El script crea los siguientes registros de prueba:

#### Empresas (3)
- **Constructora Edificar S.A.S.** (NIT: 900123456-1)
  - Sector: Construcción
  - 4 empleados
  
- **Manufacturas del Norte Ltda.** (NIT: 800987654-2)
  - Sector: Manufactura
  - 3 empleados
  
- **Servicios Empresariales Integrales S.A.** (NIT: 700555666-3)
  - Sector: Servicios
  - 3 empleados

#### Empleados (10)
Distribuidos entre las 3 empresas, con datos realistas incluyendo:
- Información personal (nombres, documentos, correos)
- Datos laborales (cargo, salario, fecha de ingreso)
- Información bancaria (banco, tipo de cuenta, número)

#### Afiliados (3)
Personas afiliadas a pólizas de salud:
- Diana Torres Mendoza - Póliza POL-2024-001
- Andrés López Gutiérrez - Póliza POL-2024-002
- Claudia Moreno Silva - Póliza POL-2024-003

#### Incapacidades ARL (3)
Incapacidades relacionadas con empleados de empresas:

1. **INC-ARL-2024-001** - Carlos Rodríguez (Constructora Edificar)
   - Diagnóstico: Fractura de radio distal derecho (CIE-10: S52.5)
   - Duración: 14 días
   - Estado: APROBADA
   - Valor: $1,400,000

2. **INC-ARL-2024-002** - Patricia Vargas (Manufacturas del Norte)
   - Diagnóstico: Contusión dedo índice (CIE-10: S61.0)
   - Duración: 7 días
   - Estado: APROBADA
   - Valor: $840,000

3. **INC-ARL-2024-003** - Ana Martínez (Constructora Edificar)
   - Diagnóstico: Lumbalgia aguda (CIE-10: M54.5)
   - Duración: 7 días
   - Estado: EN_AUDITORIA
   - Valor: $665,000

#### Incapacidades SALUD (4)
Incapacidades relacionadas con afiliados a pólizas:

1. **INC-SALUD-2024-001** - Diana Torres
   - Diagnóstico: Faringitis aguda (CIE-10: J02.9)
   - Duración: 7 días
   - Estado: APROBADA
   - Valor: $560,000

2. **INC-SALUD-2024-002** - Andrés López
   - Diagnóstico: Gastroenteritis aguda (CIE-10: K52.9)
   - Duración: 14 días
   - Estado: APROBADA
   - Valor: $1,120,000

3. **INC-SALUD-2024-003** - Claudia Moreno
   - Diagnóstico: Migraña con aura (CIE-10: G43.1)
   - Duración: 7 días
   - Estado: RADICADA

4. **INC-SALUD-2024-004** - Diana Torres (segunda incapacidad)
   - Diagnóstico: Cefalea tensional (CIE-10: G44.2)
   - Duración: 3 días
   - Estado: EN_AUDITORIA

### Estados Disponibles

Las incapacidades creadas tienen diferentes estados para facilitar pruebas del workflow:

- **APROBADA** (5): Listas para probar módulo de documentos y órdenes de pago
- **EN_AUDITORIA** (2): Para probar workflow de auditoría
- **RADICADA** (1): Para probar radicación y estados iniciales

### Archivos PDF para Pruebas

El script hace referencia a los archivos PDF disponibles en `backend/pdf_documentos/`:
- `incapacidad.pdf` - Certificado de incapacidad médica
- `historia clínica.pdf` - Historia clínica del paciente
- `medicamentos.pdf` - Fórmula médica y medicamentos

### Prerrequisitos

El script requiere:
1. Base de datos PostgreSQL con migraciones aplicadas
2. Usuario admin existente (se busca automáticamente)
3. Enums de PostgreSQL creados por las migraciones

### Notas Importantes

- **Siniestros omitidos**: Actualmente se omite la creación de siniestros porque los enums de PostgreSQL (`GravedadSiniestro`, `EstadoSiniestro`) no existen en la base de datos actual. Las migraciones deben actualizarse para crear estos enums.

- **Datos idempotentes**: El script puede ejecutarse múltiples veces. Cada ejecución creará nuevos registros con IDs únicos (UUID v4).

- **Limpieza manual**: Si deseas limpiar los datos de prueba:
  ```sql
  DELETE FROM incapacidad WHERE numero LIKE 'INC-%2024%';
  DELETE FROM empleado WHERE email LIKE '%@constructora%' OR email LIKE '%@manufacturas%';
  DELETE FROM afiliado WHERE numero_poliza LIKE 'POL-2024%';
  DELETE FROM empresa WHERE nit IN ('900123456-1', '800987654-2', '700555666-3');
  ```

### Próximos Pasos

Una vez ejecutado el script, puedes:
1. **Probar endpoints** de incapacidades via Swagger UI
2. **Implementar módulo de documentos** usando las incapacidades APROBADA
3. **Validar workflow** cambiando estados de incapacidades
4. **Crear órdenes de pago** para las incapacidades aprobadas

### Solución de Problemas

**Error: "Usuario admin no encontrado"**
- Ejecuta primero las migraciones de Alembic
- Asegúrate de crear un usuario con rol ADMIN

**Error: "column X does not exist"**
- Verifica que las migraciones estén actualizadas
- Compara el modelo SQLAlchemy con la estructura de la BD

**Error: "enum X does not exist"**
- Los enums deben crearse en las migraciones de Alembic
- Revisa las migraciones en `backend/alembic/versions/`
