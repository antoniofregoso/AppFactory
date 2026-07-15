# Dominio talent
vamos a crear el dominio talent.
el primer modelo sera 
`talent.agent`
vas a usar 
```python
class AgentType(str, Enum):
    HUMAN = "HUMAN"
    AIAGENT = "AIAGENT"
```
para definir type

lleva `id`, `uuid`, `name`, `type`, `active`, `sequence`, `color` y  `avatar_url`,`party_id` y `company_id` como 

## Campos adicionales para ubicar la posicio de cada agente
talent.system
------
id
uuid
name
description

talent.area
----
id
uuid
system_id
name
description

talent.position
--------
id
uuid
area_id
name
mission



`party_id` es obligatorio porque ahi van los campos de contacto

puedes proponer campos adicionales.

Crea solo el modelo. Cuando quede bien hacemos lo demas 

## Pendientes para el cierre del dominio talent

- Agregar índices GIN para los campos JSONB multilenguaje.
- Agregar índices de búsqueda textual para `description` y `mission`, considerando que contienen HTML generado con Quill.
- Registrar los modelos `talent.*` en la búsqueda global con aislamiento por compañía.
- Exponer una interfaz MCP de solo lectura para consultar sistemas, áreas, posiciones, agentes y el organigrama.
- Definir y validar los permisos por compañía antes de permitir mutaciones mediante MCP.
