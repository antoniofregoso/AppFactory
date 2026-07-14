# Tareas pendientes

## Plantilla genérica y dominios

- [ ] Definir la estructura base de la plantilla genérica para soportar múltiples negocios (hostal y renta de minibodekas).
- [ ] Establecer la convención de nombres y organización del código para los nuevos dominios, empezando por `parties.model`.
- [x] Implementar el dominio `parties` con su capa de modelo, servicios, contratos y endpoints iniciales.
- [ ] Definir cómo se reutilizará la misma arquitectura para el dominio `talent` sin duplicar lógica de negocio.
- [ ] Preparar los puntos de extensión para configuraciones específicas por negocio, manteniendo un núcleo común.
- [ ] Crear una primera versión de pruebas base para `parties` y dejar el camino listo para extenderlas a `talent`.

## Archivos adjuntos

- [x] Implementar inicialmente un filestore local persistente para documentos e imágenes asociados a los registros.
- [x] Guardar en PostgreSQL únicamente los metadatos y la ruta relativa del archivo, nunca el contenido binario.
- [x] Mantener el acceso al almacenamiento detrás de una interfaz intercambiable para evitar acoplar el dominio al disco local.
- [ ] Antes de producción, migrar el filestore a un bucket privado de Cloudflare R2.
- [ ] En producción, subir y descargar mediante URLs firmadas de corta duración, conservando la validación de permisos en el backend.
- [ ] Preparar y verificar la migración de archivos locales a R2, incluyendo checksums, conteo de objetos y estrategia de respaldo/rollback.
