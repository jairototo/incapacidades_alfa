Buenos días, este es el reporte de los cambios realizados estos días:

# 📋 Reporte de Avances — Sistema de Incapacidades
*Período: 11 de junio de 2026*

## 1. Reorganización general del proyecto
Se ordenó toda la estructura de carpetas del sistema para que sea más clara, mantenible y fácil de escalar. Backend, frontend externo y sistema interno quedaron en directorios separados y bien identificados.

## 2. Módulo de almacenamiento seguro de archivos
Se implementó el sistema que guarda los documentos que suben los empleados y empresas. Funciona con almacenamiento local en el servidor y también es compatible con servicios en la nube (MinIO/S3) para cuando el volumen de archivos crezca.

## 3. Autenticación de usuarios completada

Se completó el módulo de inicio de sesión con tokens seguros (JWT). El sistema valida quién entra, por cuánto tiempo, y cierra la sesión automáticamente cuando expira. Incluye pruebas automatizadas que verifican que todo funcione correctamente.

## 4. Notificaciones automáticas por correo electrónico
Cada vez que un empleado radica una incapacidad, el sistema envía automáticamente un correo de confirmación. Las notificaciones se envían en segundo plano para no ralentizar la aplicación.

## 5. Formulario de radicación simplificado: de 5 pasos a 2

El proceso para que un empleado radique una incapacidad pasó de ser un formulario de 5 pasos a uno de solo 2. En el primer paso se registran los datos del empleado, la empresa y el tipo de incapacidad. En el segundo se ingresan los datos médicos y se adjuntan los documentos. El proceso es más rápido y claro para el usuario final.

📷 [Screenshot aquí]

---

## 6. Vista previa de documentos adjuntos

Los documentos que adjuntan los empleados ahora se pueden ver directamente en pantalla sin necesidad de descargarlos. Las imágenes se muestran como miniatura y los PDFs se abren en un visor integrado dentro de la aplicación.

📷 [Screenshot aquí]

---

## 7. Validaciones automáticas al recibir una radicación

Cuando llega una incapacidad radicada, el sistema la analiza automáticamente antes de enviarla a auditoría. Verifica que el empleado y la empresa estén registrados, que los datos médicos sean consistentes y detecta posibles irregularidades. Cada alerta queda registrada con su nivel de gravedad.

📷 [Screenshot aquí]

---

## 8. Procesamiento automático de la radicación

Una vez que el sistema completa las validaciones, convierte la radicación en una incapacidad formal y la envía directamente a auditoría con toda la información lista. Los documentos adjuntos se trasladan automáticamente y todo el proceso queda registrado con trazabilidad completa.

📷 [Screenshot aquí]

---

## 9. Información de contexto en la pestaña de auditoría

Cuando un auditor revisa una incapacidad, ahora ve un resumen compacto en la parte superior con los datos clave: nombre del empleado, empresa, código de diagnóstico y período de incapacidad. Así no necesita cambiar de pestaña para consultar esa información.

📷 [Screenshot aquí]

---

## 10. Pestaña de validaciones en el módulo de auditoría

Se agregó una pestaña dedicada que muestra todas las inconsistencias detectadas durante el procesamiento de la radicación, organizadas por categoría y ordenadas por gravedad. El auditor llega con un resumen claro de qué revisar sin tener que buscar la información manualmente.

📷 [Screenshot aquí]

---

## 11. Corrección de seguridad en el acceso a documentos

Se corrigió un problema donde los documentos del sistema no verificaban correctamente si el usuario estaba autenticado antes de mostrarlos. Ahora todas las rutas de documentos exigen sesión válida y los permisos correspondientes según el rol del usuario.

📷 [Screenshot aquí]

---

## 12. Actualización de seguridad de las aplicaciones

Se actualizaron las librerías de ambas aplicaciones web (portal externo y sistema interno) para cerrar vulnerabilidades conocidas. Antes de la actualización se detectaban 29 vulnerabilidades (2 críticas). Después de aplicar los parches el conteo quedó en cero.

📷 [Screenshot aquí]

---

## 13. Pipeline de pruebas automáticas

Se configuró un sistema de verificación automática: cada vez que se sube código nuevo, se corren todas las pruebas del backend y del frontend antes de que el cambio llegue a producción. Si algo falla, el sistema avisa de inmediato para que se corrija antes de afectar a los usuarios.

📷 [Screenshot aquí]

---

*Reporte generado el 11 de junio de 2026*
