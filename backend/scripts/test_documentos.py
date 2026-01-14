#!/usr/bin/env python3
"""
Script para probar el módulo de documentos con datos reales.
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Agregar el directorio app al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from app.db.session import AsyncSessionLocal
from app.services.documento_service import DocumentoService


async def main():
    """Prueba el módulo de documentos con datos reales."""
    
    print("🧪 Iniciando prueba del módulo de documentos\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Buscar una incapacidad APROBADA
        print("📋 Buscando incapacidad de prueba...")
        result = await session.execute(
            text("""
                SELECT id, numero, tipo, estado 
                FROM incapacidad 
                WHERE estado = 'APROBADA' 
                LIMIT 1
            """)
        )
        incapacidad = result.first()
        
        if not incapacidad:
            print("❌ No se encontraron incapacidades APROBADA en la BD")
            print("   Ejecuta primero: docker-compose exec -T api python scripts/seed_test_data.py")
            return
        
        incapacidad_id = incapacidad.id
        print(f"✅ Encontrada: {incapacidad.numero} ({incapacidad.tipo}) - {incapacidad.estado}")
        print(f"   ID: {incapacidad_id}\n")
        
        # 2. Buscar usuario admin
        result = await session.execute(
            text("SELECT id, username FROM usuario LIMIT 1")
        )
        usuario = result.first()
        
        if not usuario:
            print("❌ No se encontró usuario en la BD")
            return
        
        user_id = usuario.id
        print(f"👤 Usuario: {usuario.username}")
        print(f"   ID: {user_id}\n")
        
        # 3. Verificar si existe el archivo PDF
        pdf_path = Path(__file__).parent.parent / "pdf_documentos" / "incapacidad.pdf"
        
        if not pdf_path.exists():
            print(f"❌ Archivo no encontrado: {pdf_path}")
            print("   Creando archivo de prueba...")
            pdf_path.parent.mkdir(exist_ok=True)
            pdf_path.write_text("%PDF-1.4\nTest PDF content")
        
        print(f"📄 Archivo: {pdf_path}")
        print(f"   Tamaño: {pdf_path.stat().st_size} bytes\n")
        
        # 4. Subir documento
        print("⬆️  Subiendo documento a MinIO...")
        service = DocumentoService(db=session)
        
        with open(pdf_path, "rb") as file:
            try:
                documento = await service.upload_documento(
                    incapacidad_id=incapacidad_id,
                    file_data=file,
                    filename="incapacidad.pdf",
                    content_type="application/pdf",
                    tipo_documento="INCAPACIDAD_MEDICA",
                    uploaded_by_id=user_id
                )
                
                print(f"✅ Documento subido exitosamente!")
                print(f"   ID: {documento.id}")
                print(f"   Nombre: {documento.nombre_original}")
                print(f"   Ruta storage: {documento.ruta_storage}")
                print(f"   Hash MD5: {documento.hash_md5}")
                print(f"   Tamaño: {documento.tamanio_bytes} bytes ({documento.tamanio_mb} MB)\n")
                
                # 5. Generar URL de descarga
                print("⬇️  Generando URL de descarga...")
                url = await service.get_download_url(documento.id, expires_hours=1)
                print(f"✅ URL generada (válida por 1 hora):")
                print(f"   {url[:80]}...\n")
                
                # 6. Listar documentos de la incapacidad
                print(f"📂 Listando documentos de incapacidad {incapacidad.numero}...")
                documentos = await service.list_by_incapacidad(incapacidad_id)
                print(f"✅ Total documentos: {len(documentos)}")
                for doc in documentos:
                    print(f"   - {doc.nombre_original} ({doc.tipo_documento}) - {doc.tamanio_mb} MB")
                
                print("\n" + "="*60)
                print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
                print("="*60)
                print("\nPuedes probar los endpoints con:")
                print(f"  - GET /api/v1/documentos/{documento.id}")
                print(f"  - GET /api/v1/documentos/{documento.id}/download")
                print(f"  - GET /api/v1/documentos/incapacidades/{incapacidad_id}")
                print("\nAccede a Swagger UI: http://localhost:8010/docs")
                
            except Exception as e:
                print(f"❌ Error subiendo documento: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
