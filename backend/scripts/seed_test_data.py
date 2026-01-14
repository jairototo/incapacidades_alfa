"""
Script para crear datos de prueba en la base de datos.

Crea:
- 2-3 empresas
- 5-10 empleados
- 2-3 afiliados
- 5-7 incapacidades (ARL y SALUD)
- 1-2 siniestros
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import random
import uuid

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.utils.enums import (
    TipoIncapacidad, EstadoIncapacidad, Prioridad,
    EstadoEmpresa, TipoEmpresa, EstadoEmpleado,
    EstadoAfiliado, TipoPoliza, TipoDocumento, Genero,
    TipoCuenta, SyncSource, TipoSiniestro, GravedadSiniestro, EstadoSiniestro
)


class TestDataSeeder:
    """Clase para sembrar datos de prueba."""
    
    def __init__(self):
        self.empresas_ids = []
        self.empleados_ids = []
        self.afiliados_ids = []
        self.siniestros_ids = []
        self.admin_id = None
    
    async def run(self):
        """Ejecuta el seeding de datos."""
        async with AsyncSessionLocal() as session:
            print("🌱 Iniciando seeding de datos de prueba...")
            
            # 1. Obtener admin user
            await self.get_admin_user(session)
            
            # 2. Crear empresas
            await self.create_empresas(session)
            
            # 3. Crear empleados
            await self.create_empleados(session)
            
            # 4. Crear afiliados
            await self.create_afiliados(session)
            
            # 5. Crear siniestros
            print("\n⚠️  Creando siniestros...")
            print("  ⏭️  OMITIDO: Los enums de siniestro no existen en la BD actual")
            # await self.create_siniestros(session)
            
            # 6. Crear incapacidades ARL
            await self.create_incapacidades_arl(session)
            
            # 7. Crear incapacidades SALUD
            await self.create_incapacidades_salud(session)
            
            await session.commit()
            
            print("\n✅ Seeding completado exitosamente!")
            await self.print_summary(session)
    
    async def get_admin_user(self, session: AsyncSession):
        """Obtiene el ID del usuario admin."""
        result = await session.execute(
            text("SELECT id FROM usuario WHERE username = :username"),
            {"username": "admin"}
        )
        row = result.fetchone()
        if row:
            self.admin_id = row[0]
            print(f"✅ Usuario admin encontrado: {self.admin_id}")
        else:
            print("⚠️  Usuario admin no encontrado. Algunas relaciones quedarán en NULL.")
    
    async def create_empresas(self, session: AsyncSession):
        """Crea empresas de prueba."""
        print("\n📋 Creando empresas...")
        
        empresas = [
            {
                "nit": "900123456-1",
                "razon_social": "Constructora Edificar S.A.S.",
                "email_contacto": "rrhh@edificar.com.co",
                "telefono": "+57 1 234 5678",
                "direccion": "Calle 100 # 15-20",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "tipo_empresa": TipoEmpresa.ARL.value,
                "estado": EstadoEmpresa.ACTIVA.value,
                "sync_source": SyncSource.MANUAL.value
            },
            {
                "nit": "800987654-2",
                "razon_social": "Manufacturas del Norte Ltda.",
                "email_contacto": "administracion@manufnorte.com",
                "telefono": "+57 5 765 4321",
                "direccion": "Carrera 45 # 67-89",
                "ciudad": "Barranquilla",
                "departamento": "Atlántico",
                "tipo_empresa": TipoEmpresa.ARL.value,
                "estado": EstadoEmpresa.ACTIVA.value,
                "sync_source": SyncSource.API.value
            },
            {
                "nit": "700555666-3",
                "razon_social": "Servicios Empresariales Integrales S.A.",
                "email_contacto": "contacto@sei.com.co",
                "telefono": "+57 4 555 6666",
                "direccion": "Avenida 80 # 30-50",
                "ciudad": "Medellín",
                "departamento": "Antioquia",
                "tipo_empresa": TipoEmpresa.MIXTO.value,
                "estado": EstadoEmpresa.ACTIVA.value,
                "sync_source": SyncSource.MANUAL.value
            }
        ]
        
        for empresa in empresas:
            empresa_id = uuid.uuid4()
            self.empresas_ids.append(empresa_id)
            
            await session.execute(
                text("""
                    INSERT INTO empresa (
                        id, nit, razon_social, email_contacto, telefono,
                        direccion, ciudad, departamento, tipo_empresa, estado,
                        sync_source, created_at, updated_at
                    ) VALUES (
                        :id, :nit, :razon_social, :email_contacto, :telefono,
                        :direccion, :ciudad, :departamento, :tipo_empresa, :estado,
                        :sync_source, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {"id": empresa_id, **empresa}
            )
            
            print(f"  ✅ {empresa['razon_social']} (NIT: {empresa['nit']})")
    
    async def create_empleados(self, session: AsyncSession):
        """Crea empleados de prueba."""
        print("\n👥 Creando empleados...")
        
        empleados = [
            # Empresa 1: Constructora Edificar (3 empleados)
            {
                "empresa_id": self.empresas_ids[0],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "52123456",
                "nombres": "María",
                "apellidos": "González Pérez",
                "email": "maria.gonzalez@edificar.com.co",
                "telefono": "+57 310 123 4567",
                "fecha_nacimiento": date(1985, 3, 15),
                "genero": Genero.F.value,
                "cargo": "Ingeniera Civil",
                "area": "Construcción",
                "fecha_ingreso": date(2020, 1, 15),
                "salario_base": Decimal("4500000"),
                "cuenta_bancaria": "12345678901",
                "banco": "Bancolombia",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[0],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "79876543",
                "nombres": "Carlos",
                "apellidos": "Rodríguez Jiménez",
                "email": "carlos.rodriguez@edificar.com.co",
                "telefono": "+57 315 987 6543",
                "fecha_nacimiento": date(1990, 7, 22),
                "genero": Genero.M.value,
                "cargo": "Operario de Construcción",
                "area": "Obras",
                "fecha_ingreso": date(2021, 6, 1),
                "salario_base": Decimal("1500000"),
                "cuenta_bancaria": "98765432109",
                "banco": "Davivienda",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[0],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "1023456789",
                "nombres": "Ana",
                "apellidos": "Martínez López",
                "email": "ana.martinez@edificar.com.co",
                "telefono": "+57 320 456 7890",
                "fecha_nacimiento": date(1988, 11, 5),
                "genero": Genero.F.value,
                "cargo": "Coordinadora de Seguridad",
                "area": "HSE",
                "fecha_ingreso": date(2019, 3, 10),
                "salario_base": Decimal("3500000"),
                "cuenta_bancaria": "45678901234",
                "banco": "Banco de Bogotá",
                "tipo_cuenta": TipoCuenta.CORRIENTE.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            
            # Empresa 2: Manufacturas del Norte (4 empleados)
            {
                "empresa_id": self.empresas_ids[1],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "8765432",
                "nombres": "Luis",
                "apellidos": "Hernández Castro",
                "email": "luis.hernandez@manufnorte.com",
                "telefono": "+57 300 111 2222",
                "fecha_nacimiento": date(1983, 4, 18),
                "genero": Genero.M.value,
                "cargo": "Supervisor de Producción",
                "area": "Manufactura",
                "fecha_ingreso": date(2018, 8, 20),
                "salario_base": Decimal("3200000"),
                "cuenta_bancaria": "11223344556",
                "banco": "Bancolombia",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[1],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "52987654",
                "nombres": "Patricia",
                "apellidos": "Vargas Moreno",
                "email": "patricia.vargas@manufnorte.com",
                "telefono": "+57 301 333 4444",
                "fecha_nacimiento": date(1992, 9, 12),
                "genero": Genero.F.value,
                "cargo": "Operaria de Máquinas",
                "area": "Producción",
                "fecha_ingreso": date(2022, 2, 1),
                "salario_base": Decimal("1800000"),
                "cuenta_bancaria": "66778899001",
                "banco": "BBVA",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[1],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "1098765432",
                "nombres": "Jorge",
                "apellidos": "Díaz Ramírez",
                "email": "jorge.diaz@manufnorte.com",
                "telefono": "+57 302 555 6666",
                "fecha_nacimiento": date(1987, 6, 25),
                "genero": Genero.M.value,
                "cargo": "Técnico de Mantenimiento",
                "area": "Mantenimiento",
                "fecha_ingreso": date(2020, 10, 15),
                "salario_base": Decimal("2500000"),
                "cuenta_bancaria": "22334455667",
                "banco": "Davivienda",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[1],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "39876543",
                "nombres": "Sandra",
                "apellidos": "Gómez Torres",
                "email": "sandra.gomez@manufnorte.com",
                "telefono": "+57 303 777 8888",
                "fecha_nacimiento": date(1995, 1, 30),
                "genero": Genero.F.value,
                "cargo": "Asistente Administrativa",
                "area": "Administración",
                "fecha_ingreso": date(2023, 4, 1),
                "salario_base": Decimal("1600000"),
                "cuenta_bancaria": "88990011223",
                "banco": "Banco de Bogotá",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            
            # Empresa 3: Servicios Empresariales (3 empleados)
            {
                "empresa_id": self.empresas_ids[2],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "71234567",
                "nombres": "Roberto",
                "apellidos": "Sánchez Ortiz",
                "email": "roberto.sanchez@sei.com.co",
                "telefono": "+57 304 999 0000",
                "fecha_nacimiento": date(1981, 12, 8),
                "genero": Genero.M.value,
                "cargo": "Gerente de Operaciones",
                "area": "Gerencia",
                "fecha_ingreso": date(2017, 5, 1),
                "salario_base": Decimal("6500000"),
                "cuenta_bancaria": "33445566778",
                "banco": "Bancolombia",
                "tipo_cuenta": TipoCuenta.CORRIENTE.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[2],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "52345678",
                "nombres": "Laura",
                "apellidos": "Ramírez Vega",
                "email": "laura.ramirez@sei.com.co",
                "telefono": "+57 305 111 2223",
                "fecha_nacimiento": date(1993, 8, 14),
                "genero": Genero.F.value,
                "cargo": "Analista de Recursos Humanos",
                "area": "RRHH",
                "fecha_ingreso": date(2021, 9, 15),
                "salario_base": Decimal("2800000"),
                "cuenta_bancaria": "55667788990",
                "banco": "BBVA",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            },
            {
                "empresa_id": self.empresas_ids[2],
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "1087654321",
                "nombres": "Miguel",
                "apellidos": "Castro Ruiz",
                "email": "miguel.castro@sei.com.co",
                "telefono": "+57 306 333 4445",
                "fecha_nacimiento": date(1989, 2, 20),
                "genero": Genero.M.value,
                "cargo": "Conductor",
                "area": "Logística",
                "fecha_ingreso": date(2022, 7, 1),
                "salario_base": Decimal("1900000"),
                "cuenta_bancaria": "66778899112",
                "banco": "Davivienda",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoEmpleado.ACTIVO.value
            }
        ]
        
        for empleado in empleados:
            empleado_id = uuid.uuid4()
            self.empleados_ids.append(empleado_id)
            
            await session.execute(
                text("""
                    INSERT INTO empleado (
                        id, empresa_id, tipo_documento, numero_documento,
                        nombres, apellidos, email, telefono, fecha_nacimiento,
                        genero, cargo, area, fecha_ingreso, salario_base,
                        cuenta_bancaria, banco, tipo_cuenta, estado,
                        created_at, updated_at
                    ) VALUES (
                        :id, :empresa_id, :tipo_documento, :numero_documento,
                        :nombres, :apellidos, :email, :telefono, :fecha_nacimiento,
                        :genero, :cargo, :area, :fecha_ingreso, :salario_base,
                        :cuenta_bancaria, :banco, :tipo_cuenta, :estado,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {"id": empleado_id, **empleado}
            )
            
            print(f"  ✅ {empleado['nombres']} {empleado['apellidos']} - {empleado['cargo']}")
    
    async def create_afiliados(self, session: AsyncSession):
        """Crea afiliados de prueba."""
        print("\n💳 Creando afiliados...")
        
        afiliados = [
            {
                "numero_poliza": "POL-2024-001",
                "tipo_poliza": TipoPoliza.INDIVIDUAL.value,
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "41123456",
                "nombres": "Diana",
                "apellidos": "Torres Mendoza",
                "email": "diana.torres@email.com",
                "telefono": "+57 310 555 1111",
                "fecha_nacimiento": date(1987, 5, 10),
                "genero": Genero.F.value,
                "direccion": "Calle 72 # 10-34",
                "ciudad": "Bogotá",
                "departamento": "Cundinamarca",
                "fecha_inicio_poliza": date(2024, 1, 1),
                "cuenta_bancaria": "11112222333",
                "banco": "Bancolombia",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoAfiliado.ACTIVO.value
            },
            {
                "numero_poliza": "POL-2024-002",
                "tipo_poliza": TipoPoliza.FAMILIAR.value,
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "79234567",
                "nombres": "Andrés",
                "apellidos": "López Gutiérrez",
                "email": "andres.lopez@email.com",
                "telefono": "+57 320 666 2222",
                "fecha_nacimiento": date(1980, 11, 25),
                "genero": Genero.M.value,
                "direccion": "Carrera 15 # 85-40",
                "ciudad": "Medellín",
                "departamento": "Antioquia",
                "fecha_inicio_poliza": date(2023, 6, 15),
                "cuenta_bancaria": "44445555666",
                "banco": "Davivienda",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoAfiliado.ACTIVO.value
            },
            {
                "numero_poliza": "POL-2024-003",
                "tipo_poliza": TipoPoliza.INDIVIDUAL.value,
                "tipo_documento": TipoDocumento.CC.value,
                "numero_documento": "52345678",
                "nombres": "Claudia",
                "apellidos": "Moreno Silva",
                "email": "claudia.moreno@email.com",
                "telefono": "+57 315 777 3333",
                "fecha_nacimiento": date(1992, 3, 8),
                "genero": Genero.F.value,
                "direccion": "Avenida 68 # 45-67",
                "ciudad": "Cali",
                "departamento": "Valle del Cauca",
                "fecha_inicio_poliza": date(2024, 3, 1),
                "cuenta_bancaria": "77778888999",
                "banco": "BBVA",
                "tipo_cuenta": TipoCuenta.AHORROS.value,
                "estado": EstadoAfiliado.ACTIVO.value
            }
        ]
        
        for afiliado in afiliados:
            afiliado_id = uuid.uuid4()
            self.afiliados_ids.append(afiliado_id)
            
            await session.execute(
                text("""
                    INSERT INTO afiliado (
                        id, numero_poliza, tipo_poliza, tipo_documento, numero_documento,
                        nombres, apellidos, email, telefono, fecha_nacimiento,
                        genero, direccion, ciudad, departamento, fecha_inicio_poliza,
                        cuenta_bancaria, banco, tipo_cuenta, estado,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero_poliza, :tipo_poliza, :tipo_documento, :numero_documento,
                        :nombres, :apellidos, :email, :telefono, :fecha_nacimiento,
                        :genero, :direccion, :ciudad, :departamento, :fecha_inicio_poliza,
                        :cuenta_bancaria, :banco, :tipo_cuenta, :estado,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {"id": afiliado_id, **afiliado}
            )
            
            print(f"  ✅ {afiliado['nombres']} {afiliado['apellidos']} - Póliza: {afiliado['numero_poliza']}")
    
    async def create_siniestros(self, session: AsyncSession):
        """Crea siniestros de prueba."""
        print("\n⚠️  Creando siniestros...")
        
        siniestros = [
            {
                "numero_siniestro": "SIN-2024-001",
                "empleado_id": self.empleados_ids[1],  # Carlos Rodríguez - Operario
                "empresa_id": self.empresas_ids[0],  # Constructora Edificar
                "tipo_siniestro": TipoSiniestro.ACCIDENTE_TRABAJO.value,
                "fecha_siniestro": (datetime.now() - timedelta(days=30)).date(),
                "hora_siniestro": time(14, 30, 0),
                "lugar_ocurrencia": "Obra Edificio Central - Piso 5",
                "descripcion": "Caída desde andamio durante trabajos de construcción. El empleado se resbaló al realizar instalación de panel de yeso.",
                "gravedad": GravedadSiniestro.MODERADO.value,
                "estado": EstadoSiniestro.CERRADO.value,
                "testigos": "María González, supervisor de obra presente en el momento",
                "reportado_por": "Administrador del Sistema",
                "fecha_reporte": datetime.now() - timedelta(days=30),
                "requirio_hospitalizacion": False
            },
            {
                "numero_siniestro": "SIN-2024-002",
                "empleado_id": self.empleados_ids[4],  # Patricia Vargas - Operaria de Máquinas
                "empresa_id": self.empresas_ids[1],  # Manufacturas del Norte
                "tipo_siniestro": TipoSiniestro.ACCIDENTE_TRABAJO.value,
                "fecha_siniestro": (datetime.now() - timedelta(days=15)).date(),
                "hora_siniestro": time(10, 15, 0),
                "lugar_ocurrencia": "Planta de Producción - Línea 2",
                "descripcion": "Lesión en mano derecha al operar prensa industrial. Atrapamiento de dedo índice.",
                "gravedad": GravedadSiniestro.LEVE.value,
                "estado": EstadoSiniestro.CERRADO.value,
                "testigos": "Luis Hernández - Supervisor de turno",
                "reportado_por": "Administrador del Sistema",
                "fecha_reporte": datetime.now() - timedelta(days=15),
                "requirio_hospitalizacion": False
            }
        ]
        
        for siniestro in siniestros:
            siniestro_id = uuid.uuid4()
            self.siniestros_ids.append(siniestro_id)
            
            await session.execute(
                text("""
                    INSERT INTO siniestro (
                        id, numero_siniestro, empleado_id, empresa_id, tipo_siniestro,
                        fecha_siniestro, hora_siniestro, lugar_ocurrencia,
                        descripcion, gravedad, estado, testigos, reportado_por,
                        fecha_reporte, requirio_hospitalizacion,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero_siniestro, :empleado_id, :empresa_id, :tipo_siniestro,
                        :fecha_siniestro, :hora_siniestro, :lugar_ocurrencia,
                        :descripcion, :gravedad, :estado, :testigos, :reportado_por,
                        :fecha_reporte, :requirio_hospitalizacion,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {"id": siniestro_id, **siniestro}
            )
            
            print(f"  ✅ {siniestro['numero_siniestro']} - {siniestro['tipo_siniestro']} ({siniestro['gravedad']})")
    
    async def create_incapacidades_arl(self, session: AsyncSession):
        """Crea incapacidades ARL de prueba."""
        print("\n🏥 Creando incapacidades ARL...")
        
        incapacidades = [
            {
                "numero": "INC-ARL-2024-001",
                "tipo": TipoIncapacidad.ARL.value,
                "empleado_id": self.empleados_ids[1],  # Carlos Rodríguez
                "empresa_id": self.empresas_ids[0],  # Constructora Edificar
                "fecha_inicio": date.today() - timedelta(days=28),
                "fecha_fin": date.today() - timedelta(days=14),
                "dias_totales": 14,
                "diagnostico_cie10": "S52.5",
                "descripcion_diagnostico": "Fractura de radio distal derecho",
                "eps": "EPS Sura",
                "ips": "Clínica del Norte",
                "estado": EstadoIncapacidad.APROBADA.value,
                "prioridad": Prioridad.ALTA.value,
                "valor_dia": Decimal("100000"),
                "valor_total": Decimal("1400000"),
                "observaciones": "Incapacidad por accidente laboral - Caída desde andamio",
                "radicado_por_id": self.admin_id,
                "auditado_por_id": self.admin_id,
                "aprobado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=27),
                "fecha_auditoria": datetime.now() - timedelta(days=25),
                "fecha_aprobacion": datetime.now() - timedelta(days=24)
            },
            {
                "numero": "INC-ARL-2024-002",
                "tipo": TipoIncapacidad.ARL.value,
                "empleado_id": self.empleados_ids[4],  # Patricia Vargas
                "empresa_id": self.empresas_ids[1],  # Manufacturas del Norte
                "fecha_inicio": date.today() - timedelta(days=14),
                "fecha_fin": date.today() - timedelta(days=7),
                "dias_totales": 7,
                "diagnostico_cie10": "S61.0",
                "descripcion_diagnostico": "Contusión y laceración dedo índice mano derecha",
                "eps": "EPS Sanitas",
                "ips": "Centro Médico Empresarial",
                "estado": EstadoIncapacidad.APROBADA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("120000"),
                "valor_total": Decimal("840000"),
                "observaciones": "Incapacidad por accidente con maquinaria industrial",
                "radicado_por_id": self.admin_id,
                "auditado_por_id": self.admin_id,
                "aprobado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=13),
                "fecha_auditoria": datetime.now() - timedelta(days=11),
                "fecha_aprobacion": datetime.now() - timedelta(days=10)
            },
            {
                "numero": "INC-ARL-2024-003",
                "tipo": TipoIncapacidad.ARL.value,
                "empleado_id": self.empleados_ids[2],  # Ana Martínez
                "empresa_id": self.empresas_ids[0],  # Constructora Edificar
                "fecha_inicio": date.today() - timedelta(days=5),
                "fecha_fin": date.today() + timedelta(days=2),
                "dias_totales": 7,
                "diagnostico_cie10": "M54.5",
                "descripcion_diagnostico": "Lumbalgia aguda por sobreesfuerzo",
                "eps": "EPS Compensar",
                "ips": "Hospital San Rafael",
                "estado": EstadoIncapacidad.EN_AUDITORIA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("95000"),
                "valor_total": Decimal("665000"),
                "radicado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=4),
                "fecha_auditoria": datetime.now() - timedelta(days=2)
            }
        ]
        
        for incap in incapacidades:
            incap_id = uuid.uuid4()
            
            # Determinar qué campos incluir según el estado
            if incap["estado"] in [EstadoIncapacidad.APROBADA.value, EstadoIncapacidad.PAGADA.value]:
                query = """
                    INSERT INTO incapacidad (
                        id, numero, tipo, empleado_id, empresa_id,
                        fecha_inicio, fecha_fin, dias_totales, diagnostico_cie10, descripcion_diagnostico,
                        eps, ips, estado, prioridad,
                        valor_dia, valor_total, observaciones, radicado_por_id, auditado_por_id,
                        aprobado_por_id, fecha_radicacion, fecha_auditoria, fecha_aprobacion,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero, :tipo, :empleado_id, :empresa_id,
                        :fecha_inicio, :fecha_fin, :dias_totales, :diagnostico_cie10, :descripcion_diagnostico,
                        :eps, :ips, :estado, :prioridad,
                        :valor_dia, :valor_total, :observaciones, :radicado_por_id, :auditado_por_id,
                        :aprobado_por_id, :fecha_radicacion, :fecha_auditoria, :fecha_aprobacion,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """
            else:
                query = """
                    INSERT INTO incapacidad (
                        id, numero, tipo, empleado_id, empresa_id,
                        fecha_inicio, fecha_fin, dias_totales, diagnostico_cie10, descripcion_diagnostico,
                        eps, ips, estado, prioridad, valor_dia,
                        radicado_por_id, fecha_radicacion, fecha_auditoria,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero, :tipo, :empleado_id, :empresa_id,
                        :fecha_inicio, :fecha_fin, :dias_totales, :diagnostico_cie10, :descripcion_diagnostico,
                        :eps, :ips, :estado, :prioridad, :valor_dia,
                        :radicado_por_id, :fecha_radicacion, :fecha_auditoria,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """
            
            await session.execute(text(query), {"id": incap_id, **incap})
            
            print(f"  ✅ {incap['numero']} - {incap['descripcion_diagnostico'][:50]}... ({incap['estado']})")
    
    async def create_incapacidades_salud(self, session: AsyncSession):
        """Crea incapacidades SALUD de prueba."""
        print("\n💊 Creando incapacidades SALUD...")
        
        incapacidades = [
            {
                "numero": "INC-SALUD-2024-001",
                "tipo": TipoIncapacidad.SALUD.value,
                "afiliado_id": self.afiliados_ids[0],  # Diana Torres
                "fecha_inicio": date.today() - timedelta(days=10),
                "fecha_fin": date.today() - timedelta(days=3),
                "dias_totales": 7,
                "diagnostico_cie10": "J02.9",
                "descripcion_diagnostico": "Faringitis aguda no especificada",
                "eps": "EPS Sanitas",
                "ips": "Clínica 72",
                "estado": EstadoIncapacidad.APROBADA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("80000"),
                "valor_total": Decimal("560000"),
                "observaciones": "Incapacidad por enfermedad general",
                "radicado_por_id": self.admin_id,
                "auditado_por_id": self.admin_id,
                "aprobado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=9),
                "fecha_auditoria": datetime.now() - timedelta(days=7),
                "fecha_aprobacion": datetime.now() - timedelta(days=6)
            },
            {
                "numero": "INC-SALUD-2024-002",
                "tipo": TipoIncapacidad.SALUD.value,
                "afiliado_id": self.afiliados_ids[1],  # Andrés López
                "fecha_inicio": date.today() - timedelta(days=20),
                "fecha_fin": date.today() - timedelta(days=6),
                "dias_totales": 14,
                "diagnostico_cie10": "K52.9",
                "descripcion_diagnostico": "Gastroenteritis aguda no especificada",
                "eps": "EPS Nueva EPS",
                "ips": "Clínica Las Américas",
                "estado": EstadoIncapacidad.APROBADA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("80000"),
                "valor_total": Decimal("1120000"),
                "observaciones": "Requirió hospitalización por deshidratación severa",
                "radicado_por_id": self.admin_id,
                "auditado_por_id": self.admin_id,
                "aprobado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=19),
                "fecha_auditoria": datetime.now() - timedelta(days=17),
                "fecha_aprobacion": datetime.now() - timedelta(days=16)
            },
            {
                "numero": "INC-SALUD-2024-003",
                "tipo": TipoIncapacidad.SALUD.value,
                "afiliado_id": self.afiliados_ids[2],  # Claudia Moreno
                "fecha_inicio": date.today() - timedelta(days=3),
                "fecha_fin": date.today() + timedelta(days=4),
                "dias_totales": 7,
                "diagnostico_cie10": "G43.1",
                "descripcion_diagnostico": "Migraña con aura",
                "eps": "EPS Compensar",
                "ips": "Clínica Valle del Lili",
                "estado": EstadoIncapacidad.RADICADA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("80000"),
                "radicado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(days=2)
            },
            {
                "numero": "INC-SALUD-2024-004",
                "tipo": TipoIncapacidad.SALUD.value,
                "afiliado_id": self.afiliados_ids[0],  # Diana Torres (segunda incapacidad)
                "fecha_inicio": date.today() - timedelta(days=1),
                "fecha_fin": date.today() + timedelta(days=2),
                "dias_totales": 3,
                "diagnostico_cie10": "G44.2",
                "descripcion_diagnostico": "Cefalea tensional",
                "eps": "EPS Sanitas",
                "ips": "Centro Médico Colsanitas",
                "estado": EstadoIncapacidad.EN_AUDITORIA.value,
                "prioridad": Prioridad.NORMAL.value,
                "valor_dia": Decimal("80000"),
                "radicado_por_id": self.admin_id,
                "auditado_por_id": self.admin_id,
                "fecha_radicacion": datetime.now() - timedelta(hours=20),
                "fecha_auditoria": datetime.now() - timedelta(hours=4)
            }
        ]
        
        for incap in incapacidades:
            incap_id = uuid.uuid4()
            
            # Determinar qué campos incluir según el estado
            if incap["estado"] in [EstadoIncapacidad.APROBADA.value, EstadoIncapacidad.PAGADA.value]:
                query = """
                    INSERT INTO incapacidad (
                        id, numero, tipo, afiliado_id, fecha_inicio, fecha_fin, dias_totales,
                        diagnostico_cie10, descripcion_diagnostico, eps, ips, estado, prioridad,
                        valor_dia, valor_total, observaciones, radicado_por_id, auditado_por_id,
                        aprobado_por_id, fecha_radicacion, fecha_auditoria, fecha_aprobacion,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero, :tipo, :afiliado_id, :fecha_inicio, :fecha_fin, :dias_totales,
                        :diagnostico_cie10, :descripcion_diagnostico, :eps, :ips, :estado, :prioridad,
                        :valor_dia, :valor_total, :observaciones, :radicado_por_id, :auditado_por_id,
                        :aprobado_por_id, :fecha_radicacion, :fecha_auditoria, :fecha_aprobacion,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """
            elif incap["estado"] == EstadoIncapacidad.EN_AUDITORIA.value:
                query = """
                    INSERT INTO incapacidad (
                        id, numero, tipo, afiliado_id, fecha_inicio, fecha_fin, dias_totales,
                        diagnostico_cie10, descripcion_diagnostico, eps, ips, estado, prioridad, valor_dia,
                        radicado_por_id, auditado_por_id, fecha_radicacion, fecha_auditoria,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero, :tipo, :afiliado_id, :fecha_inicio, :fecha_fin, :dias_totales,
                        :diagnostico_cie10, :descripcion_diagnostico, :eps, :ips, :estado, :prioridad, :valor_dia,
                        :radicado_por_id, :auditado_por_id, :fecha_radicacion, :fecha_auditoria,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """
            else:  # RADICADA
                query = """
                    INSERT INTO incapacidad (
                        id, numero, tipo, afiliado_id, fecha_inicio, fecha_fin, dias_totales,
                        diagnostico_cie10, descripcion_diagnostico, eps, ips, estado, prioridad, valor_dia,
                        radicado_por_id, fecha_radicacion,
                        created_at, updated_at
                    ) VALUES (
                        :id, :numero, :tipo, :afiliado_id, :fecha_inicio, :fecha_fin, :dias_totales,
                        :diagnostico_cie10, :descripcion_diagnostico, :eps, :ips, :estado, :prioridad, :valor_dia,
                        :radicado_por_id, :fecha_radicacion,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """
            
            await session.execute(text(query), {"id": incap_id, **incap})
            
            print(f"  ✅ {incap['numero']} - {incap['descripcion_diagnostico']} ({incap['estado']})")
    
    async def print_summary(self, session: AsyncSession):
        """Imprime resumen de datos creados."""
        print("\n" + "="*60)
        print("📊 RESUMEN DE DATOS CREADOS")
        print("="*60)
        
        # Contar registros por tabla
        tables = {
            "Empresas": "empresa",
            "Empleados": "empleado",
            "Afiliados": "afiliado",
            # "Siniestros": "siniestro",  # Omitidos por falta de enums
            "Incapacidades ARL": "incapacidad WHERE tipo = 'ARL'",
            "Incapacidades SALUD": "incapacidad WHERE tipo = 'SALUD'"
        }
        
        for label, table in tables.items():
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"{label:.<40} {count:>3}")
        
        print("="*60)
        print("\n✅ Base de datos lista para pruebas del módulo de documentos")
        print("\n💡 Puedes usar las incapacidades con estados:")
        print("   - APROBADA: Para probar uploads de documentos")
        print("   - EN_AUDITORIA: Para probar workflow de auditoría")
        print("   - RADICADA: Para probar radicación inicial")
        print("\n📁 Archivos PDF disponibles en: backend/pdf_documentos/")
        print("   - incapacidad.pdf")
        print("   - historia clínica.pdf")
        print("   - medicamentos.pdf")


async def main():
    """Función principal."""
    seeder = TestDataSeeder()
    await seeder.run()


if __name__ == "__main__":
    asyncio.run(main())
