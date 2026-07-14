# Pendientes del schema

Ideas para evolucionar el schema declarativo del frontend:

- `required`: marcar campos obligatorios y mostrar validacion visual.
- `readonly`: permitir campos visibles pero no editables.
- `placeholder`: texto de ayuda dentro de inputs.
- `help`: descripcion corta del campo, tooltip o texto auxiliar.
- `widget`: controlar render especializado por campo, por ejemplo `money`, `badge`, `phone`, `email`, `textarea`, `image`, `tags`.
- `default`: valor inicial para crear registros.
- `relation`: metadatos de modelos relacionados para `many2one` y `many2many`.
- `domain`: filtros declarativos para campos relacionales.
- `options`: opciones propias por campo, por ejemplo precision, moneda, formato, min, max, step.
- `validation`: reglas declarativas como longitud minima, maxima, regex o rangos numericos.
- `visibility`: reglas para ocultar/mostrar campos segun valores de otros campos.
- `editable`: controlar si un campo puede editarse solo en create, solo en update o ambos.
- `list.width`: ancho preferido de columna en vista lista.
- `list.align`: alineacion de columna cuando el tipo no sea suficiente.
- `form.colspan`: permitir que un campo ocupe varias columnas.
- `form.section`: agrupar campos del formulario por secciones.
- `calendar.color`: definir de donde sale el color del evento, por ejemplo `status`.
- `kanban.card`: definir que campos aparecen dentro de la tarjeta.
- `permissions`: permisos por accion (`create`, `read`, `update`, `delete`) para ocultar botones o bloquear campos.
- `actions`: acciones declarativas por vista o registro.
- `i18n`: completar etiquetas, placeholders y ayudas por idioma.

## Constructor visual de schemas

- [ ] Crear una herramienta visual tipo Studio para construir y mantener schemas sin editar JSON manualmente.
- [ ] Usar `SystemModel` como definición del modelo y `SystemModelField` como catálogo de campos, tipos y reglas.
- [ ] Permitir crear, editar, eliminar y ordenar campos mediante drag-and-drop.
- [ ] Configurar por campo: nombre técnico, etiquetas traducidas, tipo, valor predeterminado, `required`, `readonly`, `placeholder`, `help`, validaciones y opciones del widget.
- [ ] Configurar relaciones `many2one`, `many2many` y `one2many`, incluyendo modelo relacionado, dominio y widget de presentación.
- [ ] Diseñar visualmente la ubicación de cada campo en formulario, lista, kanban y calendario.
- [ ] Incluir una previsualización en tiempo real para escritorio, tableta, móvil y temas claro/oscuro.
- [ ] Generar y guardar la configuración resultante en `SystemModelSchema.view`, manteniendo `SystemModel` y `SystemModelField` como fuente de verdad.
- [ ] Validar antes de guardar nombres duplicados, posiciones incompatibles, referencias inexistentes, tipos no soportados y configuraciones incompletas.
- [ ] Incorporar historial de versiones, comparación de cambios y restauración de una versión anterior del schema.
- [ ] Respetar permisos para separar quién puede visualizar, editar, publicar o restaurar schemas.
- [ ] Definir un flujo de borrador, previsualización y publicación para evitar que un cambio incompleto afecte inmediatamente las vistas activas.

### Criterios de aceptación iniciales

- Un usuario autorizado puede crear un modelo y sus campos desde la interfaz.
- Puede organizar al menos las vistas de formulario, lista y kanban sin escribir JSON.
- La previsualización utiliza los mismos renderers que la aplicación real.
- Al publicar, la herramienta produce un `SystemModelSchema.view` válido y consumible por las vistas actuales.
- Los errores de configuración se muestran antes de publicar y señalan el campo o la vista afectados.
