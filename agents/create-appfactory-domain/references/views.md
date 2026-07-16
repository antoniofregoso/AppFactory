# Declarative view contract

## Contents

- Two data layers
- Supported field types
- View coverage
- Form rules
- Kanban rules
- List rules
- Calendar rules
- Relation rules
- Internationalization and helpers
- Compact example
- Rendering checklist

## Two data layers

`system_models.json` describes the model and field capabilities. `system_model_schemas.json` describes how those fields appear. A database column alone does not create a useful view.

Model metadata normally contains:

```json
{
  "name": "example.record",
  "label": {"es_MX": "Registros", "en_US": "Records"},
  "search": false,
  "readonly": false,
  "group_by": false,
  "group_by_values": [],
  "tags": [],
  "fields": []
}
```

A default schema contains `name: "default"`, `use: "view"`, the logical `model`, and a `view` array. Each field may participate independently in `kanban`, `list`, `form`, and `calendar`.

## Supported field types

Use only `FieldType` values supported by `FieldControl`:

| Purpose | Types |
|---|---|
| Text | `string`, `string_i18n`, `text`, `html`, `password` |
| Numeric | `integer`, `decimal`, `monetary`, `percentage` |
| Temporal | `date`, `datetime` |
| Choice/state | `boolean`, `selection`, `status_badge`, `color` |
| Media/data | `image`, `json` |
| Relations | `many2one`, `many2one_avatar`, `one2many`, `one2many_followers`, `many2many`, `many2many_pills` |

Metadata also recognizes `one2many_kanban` and `one2many_list`, but prefer a relation type of `one2many` with `form.view: "one2many_kanban"` or `"one2many_list"` in view schemas. This matches the current form renderer.

Use `string_i18n` for short translated content and `html` for translated rich content. Both store dictionaries such as `{"es_MX": "...", "en_US": "..."}`.

## View coverage

Every visible model needs a usable form and normally a list plus kanban. Add calendar only when the model has meaningful dates. A field can be omitted from one view without being omitted from the others.

Start with this allocation:

| Field role | Kanban | List | Form | Calendar |
|---|---|---|---|---|
| Identity/name | title | first column | title | title |
| Code/secondary identity | subtitle | early column | subtitle | optional |
| Image/avatar | image | optional | image | no |
| State/type | body/group | column | column | optional color/status |
| Description | no | no | first tab | no |
| Relations | minimal | useful columns | columns/tabs | title only when useful |
| Dates | footer/body | columns | columns | start/end |

## Form rules

The form layout parser recognizes:

- `header: "image" | "title" | "subtitle"`
- `leftColumn: <number>`
- `rightColumn: <number>`
- `footer: "left" | "right"`
- `tab: <number>`

Rules:

1. Put one human-readable field in `header: "title"`. Without it the form appears empty or unusable.
2. Use a stable secondary identifier in `header: "subtitle"` when available.
3. Put an avatar/image in `header: "image"` only when it helps identify the record.
4. Use zero-based numeric positions. Keep positions unique inside each column.
5. Put the rich description field (`description`, `mission`, or equivalent) in `form.tab: 0`. It is the first tab.
6. Put related collections in later tabs: `tab: 1`, `tab: 2`, and so on.
7. For embedded collections, set `form.view` to `one2many_kanban` or `one2many_list`.
8. Repeat `required`, `readonly`, `placeholder`, and `help` inside `form` because the renderer consumes the view schema.
9. Keep `form.help` identical to the field-level `help` in model metadata.
10. Keep non-editable derived/company fields visible with `readonly: true` rather than silently dropping important context.
11. Do not put every field everywhere. Optimize the form for task flow.

Tabs currently use numeric order; they do not declare separate tab titles. The first tab is therefore determined by the lowest `tab` number.

## Kanban rules

The kanban parser recognizes:

- `header: "image" | "title" | "subtitle"`
- `leftColumn: <number>`
- `rightColumn: <number>`
- `footer: <number>`

Require a title. Use only a few high-value facts so cards remain scannable. If the model has a `color` field with selection hex values, the kanban supports a color accent/picker when update permission exists.

For grouped kanban:

- Set model `group_by` to the technical field name.
- Provide `group_by_values` with `value`, `color`, `es_MX`, and `en_US`.
- Keep those values identical to the selection values used by the field.

Do not group a model unless every normal record can map to a declared group or the UI intentionally handles an ungrouped state.

## List rules

Declare `list: {"column": N}` with unique numeric columns. Use `order: "asc" | "desc"` on the preferred initial sort field; `order: true` marks a sortable field without forcing initial direction.

Choose columns that identify and compare records. Avoid HTML, large JSON, passwords, and noisy one-to-many collections. Many-to-one and avatar relations render their display names.

Include `sequence` only when users need to see it. The list uses update permission to enable drag reordering.

## Calendar rules

A complete calendar schema needs:

- One field with `calendar.title: true`.
- One `date` or `datetime` with `calendar.startDate: true`.
- Optionally one end field with `calendar.endDate: true`; include it whenever the business record represents a range.

Use the user's meaningful name or related user as title. Keep the same start/end fields visible and editable in the form unless the model is read-only. Calendar dragging/resizing requires update permission; creation requires create permission.

## Relation rules

- Set `model` on relation metadata and schemas when inference may be ambiguous.
- Use `many2one_avatar` for people/agents with useful avatars.
- Use `many2many_pills` for compact selectable tags/permissions.
- Use `one2many` plus `form.view` for child tabs.
- Define the ORM relationship so the generic serializer can embed `{uuid, name, display_name, model}`.
- Ensure related models are registered in `MODEL_CLASS_BY_NAME` so option loading works.
- Validate that related records belong to the caller's company before writing tenant-owned relationships.

## Internationalization and helpers

Use `es_MX` and `en_US` in source JSON. Runtime adds `es` and `en` aliases. Provide bilingual:

- model labels;
- field labels;
- placeholders;
- helpers;
- selection labels;
- role/permission names and descriptions.

Every non-obvious form field should have a helper. Never leave a mysterious control below the title without explaining its purpose.

## Compact example

```json
{
  "name": "default",
  "use": "view",
  "model": "example.record",
  "view": [
    {
      "name": "name",
      "type": "string_i18n",
      "label": {"es_MX": "Nombre", "en_US": "Name"},
      "kanban": {"header": "title"},
      "list": {"column": 0, "order": "asc"},
      "form": {
        "header": "title",
        "required": true,
        "readonly": false,
        "placeholder": {"es_MX": "Nombre", "en_US": "Name"},
        "help": {"es_MX": "Nombre visible", "en_US": "Display name"}
      }
    },
    {
      "name": "description",
      "type": "html",
      "label": {"es_MX": "Descripción", "en_US": "Description"},
      "form": {
        "tab": 0,
        "required": false,
        "readonly": false,
        "placeholder": {"es_MX": "Describe el registro", "en_US": "Describe the record"},
        "help": {"es_MX": "Descripción con formato", "en_US": "Rich-text description"}
      }
    }
  ]
}
```

## Rendering checklist

Before completion, inspect the JSON and verify:

- Default schema exists for every model.
- Form has a title and at least one body/tab field.
- Description is `html` and `tab: 0`.
- Header slots are not duplicated accidentally.
- Column/tab positions are numeric and intentional.
- List columns are unique.
- Kanban title exists.
- Calendar markers are complete.
- Relation models are valid and registered.
- Helpers match metadata.
- Selection/group values use the stored enum values exactly.
- Read-only and permissions produce the expected buttons and drag behavior.
- The view renders after a fresh database setup, not only against manually edited rows.
