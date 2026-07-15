# Declarative View Format

The view schema controls how model fields appear in Kanban, list, form, and
calendar views. Field definitions remain canonical in `system_models.json`;
view placement lives in `system_model_schemas.json`.

## Field types

| Category      | Types                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------- |
| Text          |`string_i18n`,  `string`, `text`, `password`, `html`, `json`                                                                  |
| Numeric       | `integer`, `decimal`, `monetary`, `percentage`                                                                |
| Date and time | `date`, `datetime`                                                                                            |
| Visual        | `boolean`, `color`, `image`, `selection`, `status_badge`                                                      |
| Relationships | `many2one`, `many2one_avatar`, `one2many`, `one2many_kanban`, `one2many_list`, `many2many`, `many2many_pills` |

`many2one_avatar` renders the related record's avatar and display name. The
backend serializes it as an object containing `uuid`, `name`, `display_name`,
`avatar`, and `model`.

### Multilingual strings

Use `string_i18n` for short multilingual values such as names and titles. Its
form component displays an internal language selector and persists every
translation in one JSON object:

```json
{
  "en_US": "Talent manager",
  "es_MX": "Gerente de talento"
}
```

Changing the selected language updates only that property and preserves the
other translations. List, Kanban, and read-only form values resolve the current
application language with a fallback to another available translation.

New `string_i18n` values initialize as `{}`. Use `string` for non-translated
technical values such as codes and keys. Use `html` for multilingual rich text
such as descriptions and missions; new HTML values also initialize as `{}`.

The default editor languages are `es_MX` and `en_US`. A schema may provide a
different ordered list using `form.languages`:

```json
{
  "name": "name",
  "type": "string_i18n",
  "form": {
    "leftColumn": 0,
    "languages": ["es_MX", "en_US"]
  }
}
```

## Schema structure

```json
{
  "name": "default",
  "use": "view",
  "model": "user.log",
  "view": [
    {
      "name": "user_id",
      "type": "many2one_avatar",
      "model": "user.user",
      "label": {
        "en_US": "User",
        "es_MX": "Usuario"
      },
      "kanban": { "header": "title" },
      "list": { "column": 1 },
      "form": {
        "header": "title",
        "readonly": true
      }
    }
  ]
}
```

Every schema field supports:

- `name`: record property read by the renderer.
- `type`: visualization component used for the value.
- `model`: related model for relationship fields.
- `label`: localized user-facing label.
- `kanban`, `list`, `form`, and `calendar`: view-specific configuration.

Use `en_US` and `es_MX` in canonical data. The backend adds `en` and `es`
aliases to the view response.

## Read-only models

Set `readonly` on the model definition when no generic view may mutate its
records:

```json
{
  "name": "user.log",
  "readonly": true,
  "fields": []
}
```

Read-only model views hide creation, editing, deletion, archive, drag, and
communication controls. The backend must enforce the same restriction.

Use `form.readonly` for a field that is immutable within an otherwise writable
model:

```json
{
  "form": {
    "leftColumn": 0,
    "readonly": true
  }
}
```

## Kanban

Kanban grouping is configured at model level. `groupBy` contains the record
field name, while the property with that name contains the available groups.

```json
{
  "groupBy": "status",
  "status": [
    { "value": "draft", "en": "Draft", "es": "Borrador", "color": "zinc" },
    {
      "value": "confirmed",
      "en": "Confirmed",
      "es": "Confirmada",
      "color": "green"
    }
  ]
}
```

### Card regions

| Region     | Configuration              | Behavior                   |
| ---------- | -------------------------- | -------------------------- |
| Image      | `{ "header": "image" }`    | Avatar or logo on the left |
| Title      | `{ "header": "title" }`    | Primary linked card text   |
| Subtitle   | `{ "header": "subtitle" }` | Muted text below the title |
| Left body  | `{ "leftColumn": 0 }`      | Ordered body field         |
| Right body | `{ "rightColumn": 0 }`     | Ordered body field         |
| Footer     | `{ "footer": 0 }`          | Ordered footer field       |

Only one field should occupy each header role. Body and footer positions are
zero-based integers. When the title is a `many2one_avatar`, the card uses the
related name as its title and the related avatar as its header image.

![Kanban](./images/kanban.png)

![Kanban dark theme](./images/kanban_dark.png)

## List

Add `list` to include a field as a table column:

```json
{
  "name": "date",
  "type": "datetime",
  "label": {
    "en_US": "Date",
    "es_MX": "Fecha"
  },
  "list": {
    "column": 3,
    "order": "desc"
  }
}
```

- `column` controls placement from lowest to highest.
- `order: true` enables interactive sorting without an initial direction.
- `order: "asc"` or `"desc"` enables sorting and applies an initial order.
- Only one field should declare an initial order.
- Omit `list`, or set it to `false`, to hide the field.

Relationship fields continue to use their relationship renderer in a list.
For example, `many2one_avatar` displays both avatar and name in the same cell.

![List](./images/list.png)

![List dark theme](./images/list_dark.png)

## Form

Forms contain a header, two body columns, optional tabs, and a footer.

```json
{
  "form": {
    "header": "title",
    "leftColumn": 0,
    "rightColumn": 0,
    "tab": 0,
    "required": true,
    "readonly": true,
    "placeholder": {
      "en_US": "Choose a value",
      "es_MX": "Selecciona un valor"
    },
    "help": {
      "en_US": "Helpful field guidance",
      "es_MX": "Ayuda para el campo"
    }
  }
}
```

A field should declare only one placement:

- `header`: `image`, `title`, or `subtitle`.
- `leftColumn`: zero-based position in the left column.
- `rightColumn`: zero-based position in the right column.
- `tab`: zero-based tab position.

`required`, `readonly`, `placeholder`, and `help` may accompany any placement.

### Followers

The platform adds a followers field automatically. Human and AI-agent users
may follow a record; system users are excluded. Read-only models render this
field without mutation controls.

### Related Kanban cards

Use `one2many_kanban` to display related records as compact cards:

```json
{
  "name": "users",
  "type": "one2many_kanban",
  "form": {
    "tab": 0,
    "kanban_view": {
      "header": {
        "image": "avatar_url",
        "title": "name",
        "subtitle": "email"
      }
    }
  }
}
```

The header mapping references properties on each related record, not fields in
the parent schema.

### Related List view

Use `one2many_list` to display related records as compact cards:

```json
"form": {
                    "tab": 2,
                    "view": "one2many_list",
                    "function":[
                        {
                            "name": "description",
                            "type": "count|sum",
                            "label": {
                                "es_MX": "Total",
                                "en_US": "Total"
                            }
                        }
                    ],
                    "list_view": [
                        {
                            "name": "name",
                            "type": "string",
                            "label": {
                                "es_MX": "Clave",
                                "en_US": "Key"
                            }
                        },
                        {
                            "name": "description",
                            "type": "string",
                            "label": {
                                "es_MX": "Descripción",
                                "en_US": "Description"
                            }
                        }
                    ],
                    "placeholder": {
                        "es_MX": "Configuraciones",
                        "en_US": "Settings"
                    },
                    "help": {
                        "es_MX": "Configuraciones de la aplicación",
                        "en_US": "App settings"
                    }
                }
            }
```

![Form](./images/form.png)

![Form dark theme](./images/form_dark.png)

## Calendar

Calendar roles are assigned to individual fields:

```json
{
  "calendar": {
    "startDate": true,
    "endDate": true,
    "title": true
  }
}
```

An event requires a valid `startDate`. When `endDate` is empty or invalid, the
renderer uses a 30-minute duration. The event text contains its start time and
configured title.

![Calendar](./images/calendar.png)

![Calendar dark theme](./images/calendar_dark.png)

## Insights

Insights use a separate payload containing `kpis`, `gauges`, and `graphics`.
Every element requires a stable `id` so values can update without rebuilding
the entire dashboard.

Named dashboards are `SystemModelSchema` records with `use: "insight"` attached
to the read-only virtual model `system.insight`. The schema stores component IDs
and layout only. `systemModelView` hydrates those IDs with authorized values and
returns the complete insight under `model.schema`; insight responses have no
business `records`.

See [Insights Format](./INSIGHTS_FORMAT.md) and the visualization references:

- [Bar](./BAR.md)
- [Line](./LINE.md)
- [Donut](./DONUT.md)
- [Tree map](./TREEMAP.md)
- [Radar](./RADAR.md)
- [Heat map](./HEATMAP.md)
- [Sankey](./SANKEY.md)
